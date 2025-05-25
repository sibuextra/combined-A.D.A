# Installation Instructions for Combined ADA Application

## Overview

This document provides instructions for installing and running the combined ADA (Advanced Design Assistant) application, which integrates code from two repositories:
- https://github.com/Nlouis38/ada_app (Flask backend + React frontend)
- https://github.com/Nlouis38/ada (Core assistant logic and widgets)

## System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.11 or newer
- **Node.js**: 16.x or newer
- **NPM**: 8.x or newer
- **System Libraries**: 
  - build-essential (Linux) or equivalent build tools
  - Python development headers
  - portaudio development libraries
  - libxml2 and libxslt development libraries

## Installation Steps

### 1. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev python3.11-dev portaudio19-dev libxml2-dev libxslt-dev
```

#### macOS:
```bash
brew install portaudio
```

#### Windows:
- Install Visual C++ Build Tools
- Install the appropriate Python version from python.org

### 2. Set Up the Backend

1. Navigate to the server directory:
```bash
cd ada_combined/server
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Linux/macOS: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

4. Install dependencies:
```bash
pip install --upgrade pip setuptools wheel
pip install numpy==1.24.0  # Install numpy first to avoid build issues
pip install -r requirements.txt
```

5. Create a `.env` file in the server directory with the following content:
```
# --- Backend API Keys ---
# Get from ElevenLabs website
ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"

# Get from Google AI Studio (for Gemini Models)
GOOGLE_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"

# Get from Google Cloud Console (Enabled for Directions API)
MAPS_API_KEY="YOUR_Maps_API_KEY"

# --- Flask Server Settings ---
# Used for session security, generate a random string
FLASK_SECRET_KEY="a_very_strong_and_random_secret_key_please_change_me"

# --- Frontend Settings (for Backend CORS) ---
# Port the React frontend development server runs on
REACT_APP_PORT="5173" # Default for Vite. Use 3000 for Create React App, or your custom port.
```

### 3. Set Up the Frontend

1. Navigate to the client directory:
```bash
cd ada_combined/client
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### 1. Start the Backend Server

1. Navigate to the server directory and activate the virtual environment:
```bash
cd ada_combined/server
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Run the Flask application:
```bash
python app.py
```

The server should start on http://localhost:5000

### 2. Start the Frontend Development Server

1. In a new terminal, navigate to the client directory:
```bash
cd ada_combined/client
```

2. Start the development server:
```bash
npm run dev
```

The frontend should be accessible at http://localhost:5173

## Troubleshooting

### Dependency Installation Issues

- If you encounter issues with numpy, try installing it separately before other packages:
  ```bash
  pip install numpy==1.24.0
  ```

- For issues with opencv-python, try installing a pre-built wheel:
  ```bash
  pip install opencv-python==4.5.3.56 --only-binary=opencv-python
  ```

- For PyAudio installation issues:
  - On Windows, you may need to install a pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
  - On Linux, ensure you have portaudio19-dev installed
  - On macOS, ensure you have portaudio installed via Homebrew

### API Key Issues

- Ensure all API keys in the `.env` file are valid and have the necessary permissions
- For Google Gemini API, make sure you have access to the Gemini models
- For Google Maps API, ensure the Directions API is enabled in your Google Cloud Console

### Runtime Errors

- Check the Flask server logs for backend errors
- Check the browser console for frontend errors
- Ensure all environment variables are correctly set in the `.env` file

## Features

The combined application provides:

1. A web interface for interacting with the ADA assistant
2. Text and voice input capabilities
3. Real-time responses using Google's Gemini API
4. Text-to-speech using ElevenLabs
5. Widgets for weather, maps, and search functionality
6. Webcam integration for visual context

## Additional Resources

- Google Gemini API: https://ai.google.dev/
- ElevenLabs API: https://elevenlabs.io/docs
- Google Maps API: https://developers.google.com/maps/documentation
