import json
import threading
import time
import urllib.parse
from typing import Optional, Callable
import websocket


class FireworksTranscription:
    """Fireworks AI transcription for Gradio integration."""

    WEBSOCKET_URL = "ws://audio-streaming.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions/streaming"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket_client = None
        self.is_connected = False
        self.segments = {}
        self.lock = threading.Lock()
        self.transcription_callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Callable[[str], None]):
        """Set callback to receive live transcription updates."""
        self.transcription_callback = callback

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

    def _on_open(self, ws):
        """Handle WebSocket connection opening."""
        self.is_connected = True
        print("✅ Connected to Fireworks transcription service")

    def _on_message(self, ws, message):
        """Handle transcription messages from Fireworks."""
        try:
            data = json.loads(message)

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

    @staticmethod
    def _on_error(ws, error):
        """Handle WebSocket errors."""
        print(f"WebSocket error: {error}")

    def _build_complete_text(self) -> str:
        """Build complete text from all segments."""
        if not self.segments:
            return ""

        sorted_segments = sorted(self.segments.items(), key=lambda x: int(x[0]))
        return " ".join(segment[1] for segment in sorted_segments if segment[1].strip())
