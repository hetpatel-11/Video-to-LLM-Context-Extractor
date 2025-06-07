# 🚀 Video-to-LLM Context Extractor 🚀

**Turn any video into a detailed, LLM-ready PDF document. Perfect for feeding visual and transcribed context into models like Claude, GPT, and Gemini.**

Follow me on X: <https://x.com/HetPatel_____)>

<img width="741" alt="Image" src="https://github.com/user-attachments/assets/de103c1d-94bf-4fa1-ab39-3b68e221babf" />


---

## ✨ Core Features

- 🖼️ **Frame-by-Frame Capture**: Extracts video frames at set intervals to create a visual storyboard of the content.
- 🎙️ **Accurate Audio Transcription**: Converts all spoken words into a written transcript using robust speech recognition.
- 📄 **LLM-Optimized PDF Generation**: Intelligently combines captured frames and the audio transcript into a single, easy-to-read PDF.
- 🧠 **Handles Videos of Any Length**: For longer videos, the audio is automatically chunked and processed in parallel for speed and reliability.
- ✂️ **Automatic PDF Splitting**: To ensure compatibility with LLMs, output is automatically split into multiple files if the content is extensive.
- 🎨 **Sleek Glassmorphic UI**: A modern, beautiful desktop interface that's a pleasure to use.
- 🌐 **Cross-Platform**: Built with Electron to run on Windows, macOS, and Linux.

---

## 🤔 How It Works: The 30MB Limit Explained

Large Language Models often have strict limits on the size of files you can upload. For instance, **Anthropic's Claude models generally accept PDFs up to around 30MB.**

This tool is designed with that constraint in mind. Here's the process:

1.  You select a video file.
2.  The application begins extracting frames and transcribing the audio.
3.  As the PDF is being built, the tool constantly monitors its size.
4.  If the PDF is about to exceed a safe limit (set to 28MB to be cautious), it saves the current PDF and starts a new one.
5.  This results in a set of sequentially numbered PDF files (e.g., `my_video_1.pdf`, `my_video_2.pdf`, etc.) for very long videos.

This allows you to process hours of video footage and still provide the complete context to your LLM, one chunk at a time.

---

## 🚀 Quick Start: Setup & Usage

### Prerequisites
- [Python](https://www.python.org/downloads/) (3.8 or higher)
- [Node.js](https://nodejs.org/en/download/) (14 or higher) & npm

### 1. Backend Setup (Python)

First, set up the Python environment that handles all the video processing.

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/hetpatel-11/Video-to-LLM-Context-Extractor.git
cd Video-to-LLM-Context-Extractor

# Create and activate a Python virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
.\\venv\\Scripts\\activate

# Install the required Python packages
pip install -r requirements.txt
```

### 2. Frontend Setup (Electron App)

Next, navigate into the application directory and install the necessary Node.js packages.

```bash
# From the project root (Video-to-LLM-Context-Extractor/)
cd electron_app

# Install Node dependencies
npm install
```

### 3. Running the Application

Now you're ready to launch the app!

```bash
# Make sure you are inside the 'electron_app' directory
npm start
```

### Usage Steps:
1.  Once the app launches, click the **"Select Video"** button.
2.  Choose the video file you want to process.
3.  Click the **"Convert"** button. The button text will change to "Processing... Please Wait" to let you know it's working.
4.  When the process is complete, you will find the generated PDF(s) in the **same folder as your original video**.

---

## 🏗️ Project Structure

Here is an overview of the key files and directories:

```
Video-to-LLM-Context-Extractor/
├── electron_app/
│   ├── index.html         # Main application UI (HTML)
│   ├── style.css          # UI styling
│   ├── main.js            # Electron main process (app lifecycle, backend communication)
│   ├── preload.js         # Electron script for secure IPC
│   ├── renderer.js        # UI logic and frontend event handling
│   └── package.json       # Node.js dependencies and scripts
├── src/
│   └── video_to_pdf.py    # The core Python script for video/audio processing
├── requirements.txt       # Python dependencies
└── README.md              # This file!
```

---

## 🛠️ Technical Details

- **Video Processing**: Uses `OpenCV` to extract frames and `moviepy` for video manipulation.
- **Audio Transcription**: Uses `SpeechRecognition` with the Google Speech Recognition API. Long audio is chunked with `pydub` and transcribed in parallel.
- **PDF Generation**: `reportlab` is used to create the structured PDF output.
- **Desktop Framework**: The UI is an `Electron` application.
- **Backend Communication**: The Electron frontend communicates with the Python script via a child process, ensuring the UI remains responsive.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/hetpatel-11/Video-to-LLM-Context-Extractor/issues).

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🙏 Acknowledgments

- Thanks to all the open-source libraries that made this project possible
- Special thanks to the community for their support and feedback

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/hetpatel-11/Video-to-LLM-Context-Extractor/issues) page
2. Create a new issue if needed
3. Join our community discussions 
