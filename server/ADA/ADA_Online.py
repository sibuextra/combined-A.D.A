import os
import sys
import asyncio
import json
import threading
import time
import base64
import websockets
from dotenv import load_dotenv
import google.generativeai as genai

class ADA:
    def __init__(self, google_api_key, elevenlabs_api_key, maps_api_key):
        self.google_api_key = google_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.maps_api_key = maps_api_key
        
        # Initialize Google Gemini
        genai.configure(api_key=self.google_api_key)
        self.client = genai.Client(api_key=self.google_api_key)
        
        # Set up model configuration
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-live-001",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
            },
            system_instruction=self._get_system_prompt(),
            tools=self._get_tools()
        )
        
        # Initialize conversation history
        self.chat_session = self.model.start_chat(history=[])
        
        # Video frame buffer
        self.video_frames = []
        self.max_frames = 5  # Keep only the most recent frames
        
        # ElevenLabs WebSocket
        self.tts_websocket = None
        self.tts_thread = None
        self.tts_queue = asyncio.Queue()
        
        # Initialize ElevenLabs TTS if API key is provided
        if self.elevenlabs_api_key and self.elevenlabs_api_key != "YOUR_ELEVENLABS_API_KEY":
            self.tts_thread = threading.Thread(target=self._run_tts_websocket)
            self.tts_thread.daemon = True
            self.tts_thread.start()
    
    def _get_system_prompt(self):
        return """
        You are ADA (Advanced Design Assistant), a helpful AI assistant specializing in STEM fields.
        You provide concise, accurate information and assist with various tasks.
        
        When responding:
        1. Be helpful, friendly, and conversational
        2. Provide accurate information, especially for STEM topics
        3. If you don't know something, admit it rather than making up information
        4. Use tools when appropriate to access current information
        5. Keep responses concise but informative
        
        You have access to tools for:
        - Getting weather information
        - Calculating travel duration
        - Searching the web for current information
        
        You can also process images from the user's camera when available.
        """
    
    def _get_tools(self):
        return [
            {
                "name": "get_weather",
                "description": "Get current weather information for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city or location to get weather for"
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_travel_duration",
                "description": "Calculate travel duration between two locations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Ending location"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "search_web",
                "description": "Search the web for current information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    
    def process_text_input(self, text, socketio):
        """Process text input from user and generate response"""
        try:
            # Send status update
            socketio.emit('status_update', {'status': 'Processing your request...'})
            
            # Process with Gemini
            response = self._process_with_gemini(text)
            
            # Send completion status
            socketio.emit('status_update', {'status': 'Request completed'})
            
            return response
        except Exception as e:
            print(f"Error processing text input: {str(e)}")
            socketio.emit('status_update', {'status': f'Error: {str(e)}'})
            return None
    
    def process_video_frame(self, frame_data):
        """Process a video frame from the client"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(frame_data)
            
            # Add to frame buffer
            self.video_frames.append(image_bytes)
            
            # Keep only the most recent frames
            if len(self.video_frames) > self.max_frames:
                self.video_frames.pop(0)
            
            return True
        except Exception as e:
            print(f"Error processing video frame: {str(e)}")
            return False
    
    def _process_with_gemini(self, text):
        """Process text with Gemini model and handle tool calls"""
        try:
            # Include video frames if available
            content_parts = [text]
            
            # Add the most recent video frame if available
            if self.video_frames:
                content_parts.append(self.video_frames[-1])
            
            # Generate response
            response = self.chat_session.send_message(content_parts)
            
            # Check for tool calls
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        # Handle function call
                        function_name = part.function_call.name
                        function_args = json.loads(part.function_call.args)
                        
                        # Execute the appropriate function
                        if function_name == "get_weather":
                            result = self._execute_get_weather(function_args)
                        elif function_name == "get_travel_duration":
                            result = self._execute_get_travel_duration(function_args)
                        elif function_name == "search_web":
                            result = self._execute_search_web(function_args)
                        else:
                            result = {"error": f"Unknown function: {function_name}"}
                        
                        # Send the function result back to Gemini
                        response = self.chat_session.send_message(
                            {"function_response": {"name": function_name, "response": result}}
                        )
            
            # Extract text response
            text_response = response.text
            
            # Send to TTS if available
            if self.tts_websocket and self.elevenlabs_api_key != "YOUR_ELEVENLABS_API_KEY":
                asyncio.run_coroutine_threadsafe(
                    self.tts_queue.put(text_response),
                    asyncio.get_event_loop()
                )
            
            return text_response
        except Exception as e:
            print(f"Error in Gemini processing: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    def _execute_get_weather(self, args):
        """Execute the get_weather function"""
        import python_weather
        import asyncio
        
        location = args.get("location", "New York")
        
        async def get_weather_async():
            client = python_weather.Client()
            weather = await client.get(location)
            await client.close()
            
            current = weather.current
            result = {
                "location": location,
                "temperature": current.temperature,
                "description": current.description,
                "humidity": current.humidity,
                "wind_speed": current.wind_speed
            }
            return result
        
        return asyncio.run(get_weather_async())
    
    def _execute_get_travel_duration(self, args):
        """Execute the get_travel_duration function"""
        import googlemaps
        
        origin = args.get("origin", "")
        destination = args.get("destination", "")
        
        if not origin or not destination:
            return {"error": "Origin and destination are required"}
        
        try:
            gmaps = googlemaps.Client(key=self.maps_api_key)
            directions = gmaps.directions(origin, destination)
            
            if not directions:
                return {"error": "No directions found"}
            
            # Extract relevant information
            route = directions[0]
            legs = route.get('legs', [])
            
            if not legs:
                return {"error": "No route legs found"}
            
            leg = legs[0]
            result = {
                "origin": leg.get('start_address', origin),
                "destination": leg.get('end_address', destination),
                "distance": leg.get('distance', {}).get('text', 'Unknown'),
                "duration": leg.get('duration', {}).get('text', 'Unknown')
            }
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _execute_search_web(self, args):
        """Execute the search_web function"""
        from googlesearch import search
        import aiohttp
        from bs4 import BeautifulSoup
        import asyncio
        
        query = args.get("query", "")
        
        if not query:
            return {"error": "Query is required"}
        
        try:
            # Get search results
            search_results = []
            for j in search(query, num=5, stop=5, pause=1):
                search_results.append(j)
            
            # Extract content from each URL
            results = []
            
            async def extract_content(url):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            if response.status != 200:
                                return {"url": url, "title": "", "snippet": "", "content": ""}
                            
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            title = soup.title.string if soup.title else ""
                            
                            # Extract main content
                            main_content = ""
                            paragraphs = soup.find_all('p')
                            for p in paragraphs[:5]:  # Limit to first 5 paragraphs
                                text = p.get_text().strip()
                                if len(text) > 50:  # Only include substantial paragraphs
                                    main_content += text + "\n\n"
                            
                            return {
                                "url": url,
                                "title": title,
                                "snippet": main_content[:200] + "..." if len(main_content) > 200 else main_content,
                                "content": main_content[:1000]  # Limit content length
                            }
                except Exception as e:
                    print(f"Error extracting content from {url}: {str(e)}")
                    return {"url": url, "title": "", "snippet": "", "content": ""}
            
            async def process_all_urls():
                tasks = [extract_content(url) for url in search_results]
                return await asyncio.gather(*tasks)
            
            results = asyncio.run(process_all_urls())
            
            return {"results": results}
        except Exception as e:
            return {"error": str(e)}
    
    async def _tts_websocket_handler(self):
        """Handle ElevenLabs TTS WebSocket connection"""
        uri = "wss://api.elevenlabs.io/v1/text-to-speech/stream"
        
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID (Rachel)
        model_id = "eleven_turbo_v2"
        
        # WebSocket connection headers with API key
        headers = {
            "xi-api-key": self.elevenlabs_api_key
        }
        
        try:
            async with websockets.connect(uri, extra_headers=headers) as websocket:
                self.tts_websocket = websocket
                
                # Send initial connection message
                connection_message = {
                    "text": " ",  # Initial empty text
                    "voice_id": voice_id,
                    "model_id": model_id,
                    "stream_settings": {
                        "latency": 1
                    }
                }
                await websocket.send(json.dumps(connection_message))
                
                # Start listening for text to synthesize
                while True:
                    # Get text from queue
                    text = await self.tts_queue.get()
                    
                    # Send text to ElevenLabs
                    tts_message = {
                        "text": text,
                        "voice_id": voice_id,
                        "model_id": model_id,
                        "stream_settings": {
                            "latency": 1
                        }
                    }
                    await websocket.send(json.dumps(tts_message))
                    
                    # Receive audio chunks
                    while True:
                        response = await websocket.recv()
                        response_json = json.loads(response)
                        
                        # Check if this is the end of the stream
                        if response_json.get("isFinal", False):
                            break
                        
                        # Process audio chunk
                        if "audio" in response_json:
                            audio_data = response_json["audio"]
                            # Here you would emit the audio data to the client
                            # This would be handled by the Flask-SocketIO server
        except Exception as e:
            print(f"TTS WebSocket error: {str(e)}")
            self.tts_websocket = None
    
    def _run_tts_websocket(self):
        """Run the TTS WebSocket in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._tts_websocket_handler())
