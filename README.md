# README.md - Combined ADA Application

## Overview

This project combines two repositories:
- [ada_app](https://github.com/Nlouis38/ada_app): A web application with Flask backend and React frontend
- [ada](https://github.com/Nlouis38/ada): Core assistant logic and widgets

The combined application provides a conversational AI assistant with a web interface, supporting text and voice interaction, real-time responses using Google's Gemini API, and various widgets for weather, maps, and search functionality.

## Project Structure

```
ada_combined/
├── client/             # React frontend from ada_app
├── server/             # Flask backend with integrated ADA logic
│   ├── ADA/            # Core assistant logic from ada repository
│   ├── WIDGETS/        # Widget modules from ada repository
│   ├── app.py          # Main Flask application
│   ├── requirements.txt # Combined Python dependencies
│   └── .env            # Environment configuration (you need to create this)
├── INSTALLATION.md     # Detailed installation instructions
└── README.md           # This file
```

## Quick Start

1. Follow the detailed instructions in [INSTALLATION.md](./INSTALLATION.md)
2. Set up your API keys in the `.env` file
3. Start the backend server
4. Start the frontend development server
5. Access the application at http://localhost:5173

## Features

- Web interface for interacting with ADA
- Text and voice input capabilities
- Real-time responses using Google's Gemini API
- Text-to-speech using ElevenLabs
- Widgets for weather, maps, and search functionality
- Webcam integration for visual context

## Dependencies

### Backend
- Flask and Flask-SocketIO for the web server
- Google Generative AI for the Gemini API
- ElevenLabs for text-to-speech
- Various Python packages for functionality (see requirements.txt)

### Frontend
- React for the user interface
- Socket.IO for real-time communication
- Web Speech API for speech recognition
- Various React components for UI elements

## API Keys Required

- Google Gemini API key
- ElevenLabs API key
- Google Maps API key

See INSTALLATION.md for details on obtaining and configuring these keys.
