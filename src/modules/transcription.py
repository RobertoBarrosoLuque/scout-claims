import json
import threading
import time
import urllib.parse
from typing import Optional, Callable
import websocket
import soundfile as sf
import numpy as np


class FireworksTranscription:
    """Fireworks AI transcription for Gradio integration."""

    WEBSOCKET_URL = "ws://audio-streaming.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions/streaming"
    TARGET_SAMPLE_RATE = 16000
    CHUNK_SIZE_MS = 50

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket_client = None
        self.is_connected = False
        self.segments = {}
        self.lock = threading.Lock()
        self.transcription_callback: Optional[Callable[[str], None]] = None
        self._stop_event = threading.Event()

    def set_callback(self, callback: Callable[[str], None]):
        """Set callback to receive live transcription updates."""
        self.transcription_callback = callback

    def transcribe_audio_file(self, audio_file_path: str) -> str:
        """Transcribe audio file and return final result."""
        if not self._connect():
            raise Exception("Failed to connect to Fireworks transcription service")

        try:
            # Process and stream the audio file
            self._stream_audio_file(audio_file_path)

            # Wait for completion (max 30 seconds)
            timeout = 30
            start_time = time.time()
            while self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            # Get final transcription
            final_text = self._get_final_text()
            return final_text

        finally:
            self._disconnect()

    def _connect(self) -> bool:
        """Connect to Fireworks WebSocket."""
        try:
            params = urllib.parse.urlencode({"language": "en"})
            full_url = f"{self.WEBSOCKET_URL}?{params}"

            self.websocket_client = websocket.WebSocketApp(
                full_url,
                header={"Authorization": self.api_key},
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
            )

            # Start WebSocket in background thread
            ws_thread = threading.Thread(
                target=self.websocket_client.run_forever, daemon=True
            )
            ws_thread.start()

            # Wait for connection (max 5 seconds)
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            return self.is_connected

        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def _disconnect(self):
        """Disconnect from Fireworks."""
        self._stop_event.set()
        self.is_connected = False
        if self.websocket_client:
            try:
                self.websocket_client.close()
            except Exception as e:
                print(f"Error disconnecting from Fireworks: {e}")
                pass
            self.websocket_client = None

    def _process_audio_file(self, audio_file_path: str) -> np.ndarray:
        """Load and prepare audio file for streaming."""
        audio_data, sample_rate = sf.read(audio_file_path)

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Resample to target sample rate if needed
        if sample_rate != self.TARGET_SAMPLE_RATE:
            ratio = self.TARGET_SAMPLE_RATE / sample_rate
            new_length = int(len(audio_data) * ratio)
            audio_data = np.interp(
                np.linspace(0, len(audio_data) - 1, new_length),
                np.arange(len(audio_data)),
                audio_data,
            )

        return audio_data

    def _stream_audio_file(self, audio_file_path: str):
        """Stream audio file to Fireworks in chunks."""
        try:
            audio_data = self._process_audio_file(audio_file_path)
            audio_bytes = (audio_data * 32767).astype("int16").tobytes()

            # Calculate chunk size based on target duration
            chunk_size = int(self.CHUNK_SIZE_MS * self.TARGET_SAMPLE_RATE * 2 / 1000)

            # Stream audio in chunks
            for i in range(0, len(audio_bytes), chunk_size):
                if self._stop_event.is_set():
                    break

                chunk = audio_bytes[i : i + chunk_size]
                if not self._send_audio_chunk(chunk):
                    break

                # Maintain real-time pace
                time.sleep(self.CHUNK_SIZE_MS / 1000)

            # Send final checkpoint
            self._send_final_checkpoint()

        except Exception as e:
            print(f"Error streaming audio: {e}")

    def _send_audio_chunk(self, chunk: bytes) -> bool:
        """Send audio chunk to Fireworks."""
        if not self.is_connected or not self.websocket_client:
            return False

        try:
            self.websocket_client.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
            return True
        except Exception as e:
            print(f"Error sending audio chunk: {e}")
            return False

    def _send_final_checkpoint(self):
        """Send final checkpoint to indicate end of audio."""
        if self.websocket_client:
            try:
                final_message = json.dumps({"checkpoint_id": "final"})
                self.websocket_client.send(
                    final_message, opcode=websocket.ABNF.OPCODE_TEXT
                )
                time.sleep(0.5)
            except Exception as e:
                print(f"Error sending final checkpoint: {e}")

    def _on_open(self, ws):
        """Handle WebSocket connection opening."""
        self.is_connected = True
        print("✅ Connected to Fireworks transcription service")

    def _on_message(self, ws, message):
        """Handle transcription messages from Fireworks."""
        try:
            data = json.loads(message)

            # Handle final checkpoint
            if data.get("checkpoint_id") == "final":
                self._disconnect()
                return

            # Process segments
            if "segments" in data:
                with self.lock:
                    # Update segments
                    for segment in data["segments"]:
                        segment_id = segment["id"]
                        text = segment["text"]
                        self.segments[segment_id] = text

                    # Build complete current transcription
                    complete_text = self._build_complete_text()

                    # Call callback with live update
                    if self.transcription_callback and complete_text.strip():
                        self.transcription_callback(complete_text)

        except json.JSONDecodeError as e:
            print(f"Failed to parse message: {e}")
        except Exception as e:
            print(f"Error processing message: {e}")

    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        print(f"WebSocket error: {error}")

    def _build_complete_text(self) -> str:
        """Build complete text from all segments."""
        if not self.segments:
            return ""

        sorted_segments = sorted(self.segments.items(), key=lambda x: int(x[0]))
        return " ".join(segment[1] for segment in sorted_segments if segment[1].strip())

    def _get_final_text(self) -> str:
        """Get final transcription text."""
        with self.lock:
            return self._build_complete_text()
