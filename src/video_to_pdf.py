import cv2
import os
import speech_recognition as sr
from moviepy.editor import VideoFileClip
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from PIL import Image
import tempfile
import argparse
import io
from pydub import AudioSegment
import math
import concurrent.futures

class VideoToPDFConverter:
    def __init__(self, frame_interval=30, max_pages_per_pdf=50, max_filesize_mb=28):
        self.frame_interval = frame_interval
        self.temp_dir = tempfile.mkdtemp()
        self.max_pages_per_pdf = max_pages_per_pdf
        self.max_filesize_bytes = int(max_filesize_mb * 1024 * 1024) # Convert MB to bytes

    def extract_frames(self, video_path):
        frames = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return []
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % self.frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            frame_count += 1
        cap.release()
        return frames

    def _transcribe_chunk(self, chunk_path, chunk_index, total_chunks):
        recognizer = sr.Recognizer()
        print(f"Transcribing audio chunk {chunk_index + 1}/{total_chunks}...")
        try:
            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
            transcript_part = recognizer.recognize_google(audio_data)
            print(f"Chunk {chunk_index + 1} transcribed.")
            return transcript_part
        except sr.UnknownValueError:
            print(f"Chunk {chunk_index + 1}: Google Speech Recognition could not understand audio.")
        except sr.RequestError as e:
            print(f"Chunk {chunk_index + 1}: Could not request results from Google service; {e}")
        except Exception as chunk_e:
            print(f"Chunk {chunk_index + 1}: Error during transcription: {chunk_e}")
        return None # Return None for failed chunks

    def extract_audio_transcript(self, video_path):
        video = None
        temp_audio_path = None
        chunk_files = [] # Keep track of chunk files for cleanup

        try:
            video = VideoFileClip(video_path)
            if video.audio is None:
                print("Video has no audio track.")
                return ""

            temp_audio_path = os.path.join(self.temp_dir, "original_temp_audio.wav")
            video.audio.write_audiofile(temp_audio_path, codec='pcm_s16le', logger=None)

            audio_segment = AudioSegment.from_wav(temp_audio_path)
            chunk_length_ms = 60 * 1000  # 60 seconds per chunk
            num_chunks = math.ceil(len(audio_segment) / chunk_length_ms)
            print(f"Audio duration: {len(audio_segment)/(1000*60):.2f} minutes, splitting into {num_chunks} chunks for transcription.")

            futures_to_chunk_index = {}
            # Using a ThreadPoolExecutor to parallelize API calls
            # Adjust max_workers based on testing; too many might not always be better due to API rate limits or GIL for CPU-bound parts
            max_workers = min(num_chunks, 8) # e.g., up to 8 concurrent transcriptions, or fewer if fewer chunks
            if max_workers <= 0: max_workers = 1 # Ensure at least 1 worker
            
            transcript_parts = [None] * num_chunks # Pre-allocate list to store results in order

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                for i in range(num_chunks):
                    start_ms = i * chunk_length_ms
                    end_ms = (i + 1) * chunk_length_ms
                    audio_chunk = audio_segment[start_ms:end_ms]
                    
                    chunk_temp_file = os.path.join(self.temp_dir, f"chunk_{i}.wav")
                    audio_chunk.export(chunk_temp_file, format="wav")
                    chunk_files.append(chunk_temp_file) # Add to list for cleanup
                    
                    future = executor.submit(self._transcribe_chunk, chunk_temp_file, i, num_chunks)
                    futures_to_chunk_index[future] = i

                for future in concurrent.futures.as_completed(futures_to_chunk_index):
                    chunk_index = futures_to_chunk_index[future]
                    try:
                        result = future.result()
                        if result:
                            transcript_parts[chunk_index] = result
                    except Exception as exc:
                        print(f"Chunk {chunk_index + 1} generated an exception: {exc}")
            
            # Filter out None results (failed transcriptions) and join
            final_transcript = " ".join(part for part in transcript_parts if part is not None)
            if not final_transcript.strip():
                 return "Audio could not be transcribed (all chunks failed, were unintelligible, or resulted in empty strings)."
            return final_transcript

        except Exception as e:
            print(f"An unexpected error occurred during audio extraction or transcription setup: {str(e)}")
            return "Audio not transcribed (overall processing error)."
        finally:
            if video:
                video.close()
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            for chunk_file in chunk_files: # Clean up all chunk files
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
    
    def _start_new_pdf(self, output_basename, pdf_count):
        output_pdf_path = f"{output_basename}_{pdf_count}.pdf"
        c = canvas.Canvas(output_pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        return c, output_pdf_path

    def _add_text_to_pdf(self, pdf_canvas, text, x, y, line_height, page_height, right_margin):
        words = text.split()
        current_line = ""
        lines_on_page = (page_height - y - inch) // line_height
        for word in words:
            if pdf_canvas.stringWidth(current_line + word, "Helvetica", 10) < (letter[0] - x - right_margin):
                current_line += word + " "
            else:
                pdf_canvas.drawString(x, y, current_line.strip())
                y -= line_height
                current_line = word + " "
                lines_on_page -=1
                if y < inch:
                    pdf_canvas.showPage()
                    pdf_canvas.setFont("Helvetica", 10)
                    y = page_height - inch
                    lines_on_page = (page_height - y - inch) // line_height
        if current_line:
            pdf_canvas.drawString(x, y, current_line.strip())
            y -= line_height
            lines_on_page -=1
        return y, lines_on_page

    def create_pdf(self, video_path, output_basename):
        frames = self.extract_frames(video_path)
        transcript = self.extract_audio_transcript(video_path)

        if not frames and not transcript:
            print("No frames extracted and no transcript available. PDF will not be created.")
            if os.path.exists(self.temp_dir):
                try:
                    for file_name in os.listdir(self.temp_dir):
                        os.remove(os.path.join(self.temp_dir, file_name))
                    os.rmdir(self.temp_dir)
                except OSError as e:
                    print(f"Error cleaning up temp directory {self.temp_dir} on early exit: {e}")
            return

        pdf_count = 1
        current_pdf_canvas, current_pdf_path = self._start_new_pdf(output_basename, pdf_count)
        page_width, page_height = letter
        margin = 0.5 * inch
        line_height = 14
        pages_in_current_pdf = 1
        y_position = page_height - margin
        frames_header_pending_on_new_pdf = False

        def finalize_current_pdf_and_start_new():
            nonlocal current_pdf_canvas, current_pdf_path, pdf_count, pages_in_current_pdf, y_position, frames_header_pending_on_new_pdf
            if len(current_pdf_canvas.getpdfdata()) > 100: 
                 current_pdf_canvas.save()
                 print(f"Saved PDF: {current_pdf_path} (Size: {os.path.getsize(current_pdf_path) / (1024*1024):.2f} MB)")
            else:
                print(f"Skipped saving empty PDF part: {current_pdf_path}")
                if os.path.exists(current_pdf_path):
                    try: os.remove(current_pdf_path); print(f"Removed empty PDF file: {current_pdf_path}") 
                    except: pass 

            pdf_count += 1
            current_pdf_canvas, current_pdf_path = self._start_new_pdf(output_basename, pdf_count)
            pages_in_current_pdf = 1
            y_position = page_height - margin
            frames_header_pending_on_new_pdf = True 
            return True 

        if transcript:
            current_pdf_canvas.setFont("Helvetica-Bold", 12)
            current_pdf_canvas.drawString(margin, y_position, "Audio Transcript:")
            y_position -= line_height * 1.5
            current_pdf_canvas.setFont("Helvetica", 10)
            transcript_lines = transcript.split('\n')
            for line_text in transcript_lines:
                prev_y_position = y_position
                y_position, _ = self._add_text_to_pdf(current_pdf_canvas, line_text, margin, y_position, line_height, page_height, margin)
                if y_position < prev_y_position and y_position < margin + line_height: 
                    pages_in_current_pdf += 1
                    if pages_in_current_pdf > self.max_pages_per_pdf:
                        if finalize_current_pdf_and_start_new():
                             current_pdf_canvas.setFont("Helvetica-Bold", 12)
                             current_pdf_canvas.drawString(margin, y_position, "Audio Transcript (Continued):")
                             y_position -= line_height * 1.5
                             current_pdf_canvas.setFont("Helvetica", 10)
            y_position -= line_height

        if frames:
            first_frame_in_series = True 
            for i, frame_data in enumerate(frames):
                if len(current_pdf_canvas.getpdfdata()) > self.max_filesize_bytes:
                    if finalize_current_pdf_and_start_new():
                        first_frame_in_series = True 
                
                pil_image = Image.fromarray(frame_data)
                img_display_width = page_width - 2 * margin
                img_display_height = (img_display_width * pil_image.height) / pil_image.width

                if y_position - img_display_height < margin or pages_in_current_pdf >= self.max_pages_per_pdf:
                    if len(current_pdf_canvas.getpdfdata()) > self.max_filesize_bytes * 0.90: 
                         if finalize_current_pdf_and_start_new():
                            first_frame_in_series = True 
                    else:
                        current_pdf_canvas.showPage()
                        current_pdf_canvas.setFont("Helvetica", 10)
                        pages_in_current_pdf += 1
                        y_position = page_height - margin
                        first_frame_in_series = False 
                
                if frames_header_pending_on_new_pdf or (first_frame_in_series and y_position == page_height - margin) or (pages_in_current_pdf == 1 and y_position == page_height-margin and i == 0) :
                    header_text = "Video Frames:" if first_frame_in_series else "Video Frames (Continued):"
                    current_pdf_canvas.setFont("Helvetica-Bold", 12)
                    current_pdf_canvas.drawString(margin, y_position, header_text)
                    y_position -= line_height * 1.5
                    frames_header_pending_on_new_pdf = False
                    first_frame_in_series = False 

                temp_frame_path = os.path.join(self.temp_dir, f"frame_{i}.png")
                pil_image.save(temp_frame_path)
                current_pdf_canvas.drawImage(temp_frame_path, margin, y_position - img_display_height,
                                             width=img_display_width, height=img_display_height, preserveAspectRatio=True)
                os.remove(temp_frame_path)
                y_position -= (img_display_height + line_height)

        if len(current_pdf_canvas.getpdfdata()) > 100: 
            current_pdf_canvas.save()
            print(f"Saved PDF: {current_pdf_path} (Size: {os.path.getsize(current_pdf_path) / (1024*1024):.2f} MB)")
        else:
            print(f"Skipped saving potentially empty final PDF part: {current_pdf_path}")
            if os.path.exists(current_pdf_path):
                 try: os.remove(current_pdf_path); print(f"Removed empty PDF file: {current_pdf_path}") 
                 except: pass
        
        try:
            for file_name in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file_name))
            os.rmdir(self.temp_dir)
        except OSError as e:
            print(f"Error cleaning up temp directory {self.temp_dir}: {e}")

def convert_video_to_pdf(video_path, output_basename, frame_interval=30, max_pages_per_pdf=50, max_filesize_mb=28):
    converter = VideoToPDFConverter(frame_interval, max_pages_per_pdf, max_filesize_mb)
    converter.create_pdf(video_path, output_basename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a video to a PDF with frames and transcript.")
    parser.add_argument('--video', type=str, required=True, help='Path to input video file')
    parser.add_argument('--output', type=str, default="output_video_content", help='Base name for output PDF file(s)')
    parser.add_argument('--frame-interval', type=int, default=30, help='Capture one frame every N frames')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum pages per PDF before splitting (secondary to filesize)')
    parser.add_argument('--max-filesize', type=int, default=28, help='Approximate maximum filesize in MB for each PDF part (e.g., 28 for a 30MB limit)')
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Video file not found at {args.video}")
    elif args.frame_interval <= 0:
        print(f"Error: Frame interval must be positive.")
    elif args.max_pages <= 0:
        print(f"Error: Max pages per PDF must be positive.")
    elif args.max_filesize <= 0:
        print(f"Error: Max filesize must be positive.")
    else:
        convert_video_to_pdf(
            video_path=args.video,
            output_basename=args.output,
            frame_interval=args.frame_interval,
            max_pages_per_pdf=args.max_pages,
            max_filesize_mb=args.max_filesize
        ) 