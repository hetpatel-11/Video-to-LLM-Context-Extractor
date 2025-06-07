const videoPathInput = document.getElementById('videoPath');
const selectVideoBtn = document.getElementById('selectVideoBtn');
const outputDirPathInput = document.getElementById('outputDirPath');
const selectOutputDirBtn = document.getElementById('selectOutputDirBtn');
const frameIntervalInput = document.getElementById('frameInterval');
const maxPagesInput = document.getElementById('maxPages');
const maxFilesizeInput = document.getElementById('maxFilesize');
const convertBtn = document.getElementById('convertBtn');
const statusLog = document.getElementById('statusLog');

let selectedVideoPath = null;
let selectedOutputDirPath = null;

function logMessage(message, isError = false) {
    const time = new Date().toLocaleTimeString();
    statusLog.textContent += `[${time}] ${message}\n`;
    statusLog.scrollTop = statusLog.scrollHeight; // Auto-scroll
    if (isError) {
        console.error(message);
    }
}

selectVideoBtn.addEventListener('click', async () => {
    selectedVideoPath = await window.electronAPI.selectVideoFile();
    if (selectedVideoPath) {
        videoPathInput.value = selectedVideoPath;
        logMessage(`Selected video: ${selectedVideoPath}`);
    } else {
        videoPathInput.value = '';
        logMessage('Video selection canceled.');
    }
});

selectOutputDirBtn.addEventListener('click', async () => {
    selectedOutputDirPath = await window.electronAPI.selectOutputDirectory();
    if (selectedOutputDirPath) {
        outputDirPathInput.value = selectedOutputDirPath;
        logMessage(`Selected output directory: ${selectedOutputDirPath}`);
    } else {
        outputDirPathInput.value = '';
        logMessage('Output directory selection canceled.');
    }
});

convertBtn.addEventListener('click', async () => {
    if (!selectedVideoPath) {
        logMessage('Error: Please select a video file first.', true);
        alert('Please select a video file.');
        return;
    }
    if (!selectedOutputDirPath) {
        logMessage('Error: Please select an output directory first.', true);
        alert('Please select an output directory.');
        return;
    }

    const frameInterval = parseInt(frameIntervalInput.value, 10);
    const maxPages = parseInt(maxPagesInput.value, 10);
    const maxFilesize = parseInt(maxFilesizeInput.value, 10);

    if (isNaN(frameInterval) || frameInterval < 1) {
        logMessage('Error: Invalid frame interval. Must be a number >= 1.', true);
        alert('Invalid frame interval. Must be a number >= 1.');
        return;
    }
    if (isNaN(maxPages) || maxPages < 1) {
        logMessage('Error: Invalid max pages. Must be a number >= 1.', true);
        alert('Invalid max pages. Must be a number >= 1.');
        return;
    }
    if (isNaN(maxFilesize) || maxFilesize < 1) {
        logMessage('Error: Invalid max filesize. Must be a number >= 1.', true);
        alert('Error: Invalid max filesize. Must be a number >= 1.');
        return;
    }

    const videoFileName = selectedVideoPath.split(/[\\/]/).pop();
    const outputBasename = `${selectedOutputDirPath}/${videoFileName.substring(0, videoFileName.lastIndexOf('.')) || videoFileName}_content`;

    statusLog.textContent = ''; // Clear previous logs
    logMessage('Starting conversion... This may take some time depending on video length.');
    logMessage(`Video: ${selectedVideoPath}`);
    logMessage(`Output Base: ${outputBasename}`);
    logMessage(`Frame Interval: ${frameInterval}, Max Pages: ${maxPages}, Max Filesize: ${maxFilesize}MB`);
    
    convertBtn.disabled = true;
    convertBtn.textContent = 'Processing... Please Wait'; // Update button text

    window.electronAPI.removeConversionProgressListener();
    window.electronAPI.removeConversionErrorListener();

    window.electronAPI.onConversionProgress(logMessage);
    window.electronAPI.onConversionError((errorMessage) => logMessage(errorMessage, true));

    try {
        const result = await window.electronAPI.runConversion({
            videoPath: selectedVideoPath,
            outputBasename: outputBasename,
            frameInterval: frameInterval,
            maxPages: maxPages,
            maxFilesizeMb: maxFilesize
        });
        if (result.success) {
            logMessage(`Conversion successful! PDFs created in ${result.outputDir}`);
            alert(`Conversion successful! PDFs created in ${result.outputDir}`);
        } else {
            // Python script errors (stderr) are already logged by onConversionError
            // This handles cases where the promise rejects for other reasons or python script exits non-zero but no specific stderr message was caught separately
            logMessage(`Conversion process completed with issues: ${result.message || 'Unknown issue'}`, true);
        }
    } catch (error) {
        logMessage(`Application error during conversion: ${error.message}`, true);
        alert(`Application Error: ${error.message}`);
    } finally {
        convertBtn.disabled = false;
        convertBtn.textContent = 'Convert to PDF'; // Revert button text
        window.electronAPI.removeConversionProgressListener();
        window.electronAPI.removeConversionErrorListener();
    }
});

logMessage('Application ready. Please select a video and output directory.'); 