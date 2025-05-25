import os
import sys
import asyncio
import json
import base64
import time
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import threading

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import ADA core
from ADA.ADA_Online import ADA

# Load environment variables
load_dotenv()

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MAPS_API_KEY = os.getenv("MAPS_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
REACT_APP_PORT = os.getenv("REACT_APP_PORT", "5173")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins=[
    f"http://localhost:{REACT_APP_PORT}",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # For development
])

# Initialize ADA instance
ada = None
ada_thread = None
processing_lock = threading.Lock()

def initialize_ada():
    global ada
    ada = ADA(
        google_api_key=GOOGLE_API_KEY,
        elevenlabs_api_key=ELEVENLABS_API_KEY,
        maps_api_key=MAPS_API_KEY
    )

# Initialize ADA on startup
initialize_ada()

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status_update', {'status': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('send_text_message')
def handle_text_message(data):
    text = data.get('text', '')
    if not text:
        emit('status_update', {'status': 'Error: Empty message'})
        return
    
    emit('status_update', {'status': 'Processing text message...'})
    
    # Process in a separate thread to avoid blocking
    def process_message():
        with processing_lock:
            try:
                response = ada.process_text_input(text, socketio)
                
                # Send response in chunks to simulate streaming
                if response:
                    chunk_size = 10  # Characters per chunk
                    for i in range(0, len(response), chunk_size):
                        chunk = response[i:i+chunk_size]
                        socketio.emit('receive_text_chunk', {'chunk': chunk})
                        time.sleep(0.05)  # Small delay between chunks
            except Exception as e:
                print(f"Error processing text: {str(e)}")
                socketio.emit('status_update', {'status': f'Error: {str(e)}'})
    
    global ada_thread
    if ada_thread and ada_thread.is_alive():
        emit('status_update', {'status': 'Still processing previous request'})
        return
    
    ada_thread = threading.Thread(target=process_message)
    ada_thread.daemon = True
    ada_thread.start()

@socketio.on('send_transcribed_text')
def handle_transcribed_text(data):
    text = data.get('text', '')
    if not text:
        return
    
    emit('status_update', {'status': 'Processing transcribed text...'})
    
    # Process in a separate thread
    def process_transcription():
        with processing_lock:
            try:
                response = ada.process_text_input(text, socketio)
                
                # Send response in chunks to simulate streaming
                if response:
                    chunk_size = 10  # Characters per chunk
                    for i in range(0, len(response), chunk_size):
                        chunk = response[i:i+chunk_size]
                        socketio.emit('receive_text_chunk', {'chunk': chunk})
                        time.sleep(0.05)  # Small delay between chunks
            except Exception as e:
                print(f"Error processing transcription: {str(e)}")
                socketio.emit('status_update', {'status': f'Error: {str(e)}'})
    
    global ada_thread
    if ada_thread and ada_thread.is_alive():
        emit('status_update', {'status': 'Still processing previous request'})
        return
    
    ada_thread = threading.Thread(target=process_transcription)
    ada_thread.daemon = True
    ada_thread.start()

@socketio.on('send_video_frame')
def handle_video_frame(data):
    frame_data = data.get('frame', '')
    if not frame_data:
        return
    
    # Process video frame if ADA is ready
    if not processing_lock.locked():
        try:
            # Strip data URL prefix if present
            if frame_data.startswith('data:image'):
                frame_data = frame_data.split(',')[1]
            
            # Process frame in ADA
            ada.process_video_frame(frame_data)
        except Exception as e:
            print(f"Error processing video frame: {str(e)}")

# Routes
@app.route('/')
def index():
    return "ADA Combined Backend Server"

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

# Run the Flask app
if __name__ == '__main__':
    print("Starting ADA Combined Backend Server...")
    print(f"API Keys configured: Google={bool(GOOGLE_API_KEY)}, ElevenLabs={bool(ELEVENLABS_API_KEY)}, Maps={bool(MAPS_API_KEY)}")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
