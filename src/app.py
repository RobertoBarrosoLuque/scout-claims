from pathlib import Path
import gradio as gr
import threading
import queue
import numpy as np
import base64
import tempfile
import os

from modules.image_analysis import pil_to_base64_dict, analyze_damage_image
from modules.transcription import FireworksTranscription
from modules.incident_processing import process_transcript_description
from modules.claim_processing import generate_claim_report_pdf

_FILE_PATH = Path(__file__).parents[1]


class ClaimsAssistantApp:
    def __init__(self):
        self.damage_analysis = None
        self.incident_data = None
        self.live_transcription = ""
        self.transcription_lock = threading.Lock()
        self.is_recording = False
        self.transcription_service = None
        self.audio_queue = queue.Queue()
        self.final_report_pdf = None
        self.claim_reference = ""
        self.pdf_temp_path = None

    def create_interface(self):
        """Create the main Gradio interface"""

        with gr.Blocks(title="Scout Claims", theme=gr.themes.Soft()) as demo:
            # Header
            with gr.Row():
                with gr.Column():
                    gr.Markdown("# 🚗 Scout | AI Claims Assistant 🚗")
                    gr.Markdown("*Automated Insurance Claims Processing*")

            # Sidebar (API Key)
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Powered by:")
                    gr.Image(
                        value=str(_FILE_PATH / "assets/fireworks_logo.png"),
                        height=30,
                        width=100,
                        show_label=False,
                        show_download_button=False,
                        container=False,
                        show_fullscreen_button=False,
                    )

                    gr.Markdown("## ⚙️ Configuration")
                    api_key = gr.Textbox(
                        label="Fireworks AI API Key",
                        type="password",
                        placeholder="Enter your Fireworks AI API key",
                        value="",
                        info="Required for AI processing",
                    )

                    gr.Markdown("## 📋 Instructions")
                    gr.Markdown(
                        """
                    **Step 1:** Upload car damage photo(s)
                    **Step 2:** Use microphone to describe incident
                    **Step 3:** Generate and review claim report

                    *All processing happens automatically via FireworksAI*
                    """
                    )

                # Main Content Area
                with gr.Column(scale=3):
                    # Step 1: Upload Image
                    gr.Markdown("## 📷 Step 1: Upload Damage Photos 📷")
                    with gr.Row():
                        image_input = gr.Image(
                            label="Car Damage Photo", type="pil", height=300
                        )

                        with gr.Column():
                            analyze_btn = gr.Button(
                                "🔍 Analyze Damage", variant="primary"
                            )
                            damage_status = gr.Textbox(
                                label="Analysis Status",
                                value="Ready to analyze damage",
                                interactive=False,
                                lines=2,
                            )

                    # Damage Analysis Results
                    damage_results = gr.JSON(
                        label="Damage Analysis Results", visible=False
                    )

                    gr.Markdown("---")

                    # Step 2: Incident Description with Live Streaming
                    gr.Markdown("## 🎤 Step 2: Describe the Incident 🎤")

                    with gr.Accordion(
                        "💡 What to Include in Your Recording", open=True
                    ):
                        gr.Markdown(
                            """
                        **Please describe the following when you record:**

                        📅 **When & Where:**
                        - Date and time of the accident
                        - Street address or intersection

                        👥 **Who Was Involved:**
                        - Other driver's name and contact info
                        - Vehicle details (make, model, color, license plate)
                        - Any witnesses

                        🚗 **What Happened:**
                        - How the accident occurred
                        - Who was at fault and why
                        - Weather and road conditions

                        🏥 **Injuries & Damage:**
                        - Anyone hurt? How seriously?
                        - How severe is the vehicle damage?

                        """
                        )

                    with gr.Row():
                        # Direct audio input - no toggle button needed
                        with gr.Column():
                            audio_input = gr.Audio(
                                label="🎵 Record Incident Description",
                                sources=["microphone"],
                                streaming=True,
                                format="wav",
                                show_download_button=False,
                            )
                            transcription_display = gr.Textbox(
                                label="Live Transcription",
                                placeholder="Click the 'Record' button above to start recording...",
                                lines=8,
                                interactive=False,
                                autoscroll=True,
                            )

                    process_incident_btn = gr.Button(
                        "📝 Process Incident", variant="primary"
                    )

                    incident_status = gr.Textbox(
                        label="Processing Status",
                        value="Record audio first to process incident",
                        interactive=False,
                        lines=2,
                    )

                    # Incident Processing Results
                    incident_results = gr.JSON(
                        label="Incident Processing Results", visible=False
                    )

                    gr.Markdown("---")

                    # Step 3: Generate Claim Report
                    gr.Markdown("## 📄 Step 3: Generate Claim Report 📄")

                    generate_report_btn = gr.Button(
                        "🚀 Generate Claim Report", variant="primary", size="lg"
                    )

                    report_status = gr.Textbox(
                        label="Report Generation Status",
                        value="Complete steps 1 and 2 to generate report",
                        interactive=False,
                        lines=2,
                    )

                    # Final Report Display - Updated for PDF
                    with gr.Accordion(
                        "📋 Generated Claim Report (PDF)", open=False
                    ) as report_accordion:
                        # PDF Viewer using HTML iframe
                        pdf_viewer = gr.HTML(
                            value="<p style='text-align: center; color: gray;'>PDF report will appear here after generation</p>",
                            label="Claim Report PDF",
                        )

                        with gr.Row():
                            download_btn = gr.DownloadButton(
                                "💾 Download PDF Report", visible=False
                            )
                            submit_btn = gr.Button(
                                "✅ Submit Claim", variant="stop", visible=False
                            )

            # Event Handlers
            def handle_damage_analysis(image, api_key):
                if image is None:
                    return (
                        "❌ Please upload an image first",
                        gr.update(visible=False),
                    )

                if not api_key.strip():
                    return (
                        "❌ Please enter your Fireworks AI API key first",
                        gr.update(visible=False),
                    )

                try:
                    # Update status to show processing
                    yield (
                        "🔄 Analyzing damage... Please wait",
                        gr.update(visible=False),
                    )

                    image_dict = pil_to_base64_dict(image)
                    self.damage_analysis = analyze_damage_image(
                        image=image_dict, api_key=api_key
                    )

                    yield (
                        "✅ Damage analysis completed successfully!",
                        gr.update(value=self.damage_analysis, visible=True),
                    )
                    return None

                except Exception as e:
                    yield (
                        f"❌ Error analyzing damage: {str(e)}",
                        gr.update(visible=False),
                    )
                    return None

            def live_transcription_callback(text):
                """Callback for live transcription updates"""
                with self.transcription_lock:
                    self.live_transcription = text

            def initialize_transcription_service(api_key):
                """Initialize transcription service when audio starts"""
                if not api_key.strip():
                    return False

                if not self.transcription_service:
                    self.transcription_service = FireworksTranscription(api_key)
                    self.transcription_service.set_callback(live_transcription_callback)

                if not self.is_recording:
                    self.is_recording = True
                    self.live_transcription = ""
                    return self.transcription_service._connect()
                return True

            def process_audio_stream(audio_tuple, api_key):
                """Process incoming audio stream for live transcription"""
                if not audio_tuple:
                    with self.transcription_lock:
                        return self.live_transcription

                # Initialize transcription service if needed
                if not self.is_recording:
                    if not initialize_transcription_service(api_key):
                        return "❌ Failed to initialize transcription service. Check your API key."

                try:
                    sample_rate, audio_data = audio_tuple

                    # Convert audio data to proper format
                    if not isinstance(audio_data, np.ndarray):
                        audio_data = np.array(audio_data, dtype=np.float32)

                    if audio_data.dtype != np.float32:
                        if audio_data.dtype == np.int16:
                            audio_data = audio_data.astype(np.float32) / 32768.0
                        elif audio_data.dtype == np.int32:
                            audio_data = audio_data.astype(np.float32) / 2147483648.0
                        else:
                            audio_data = audio_data.astype(np.float32)

                    # Skip if audio is too quiet
                    if np.max(np.abs(audio_data)) < 0.01:
                        with self.transcription_lock:
                            return self.live_transcription

                    # Convert to mono if stereo
                    if len(audio_data.shape) > 1:
                        audio_data = np.mean(audio_data, axis=1)

                    # Resample to 16kHz if needed
                    if sample_rate != 16000:
                        ratio = 16000 / sample_rate
                        new_length = int(len(audio_data) * ratio)
                        if new_length > 0:
                            audio_data = np.interp(
                                np.linspace(0, len(audio_data) - 1, new_length),
                                np.arange(len(audio_data)),
                                audio_data,
                            )

                    # Convert to bytes and send to transcription service
                    audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()

                    if (
                        self.transcription_service
                        and self.transcription_service.is_connected
                    ):
                        self.transcription_service._send_audio_chunk(audio_bytes)

                except Exception as e:
                    print(f"Error processing audio stream: {e}")

                # Return current transcription
                with self.transcription_lock:
                    return self.live_transcription

            def handle_incident_processing(api_key):
                """Process the recorded transcription into structured incident data"""
                if not self.live_transcription.strip():
                    return (
                        "❌ No transcription available. Please record audio first.",
                        gr.update(visible=False),
                    )

                if not api_key.strip():
                    return (
                        "❌ Please enter your Fireworks AI API key first",
                        gr.update(visible=False),
                    )

                try:
                    # Update status
                    yield (
                        "🔄 Processing incident data... Please wait",
                        gr.update(visible=False),
                    )

                    # Use Fireworks to process the transcription and extract structured data
                    incident_analysis = process_transcript_description(
                        transcript=self.live_transcription, api_key=api_key
                    )

                    # Convert Pydantic model to dict for JSON display
                    self.incident_data = incident_analysis.model_dump()

                    yield (
                        "✅ Incident processing completed successfully!",
                        gr.update(value=self.incident_data, visible=True),
                    )
                    return None

                except Exception as e:
                    yield (
                        f"❌ Error processing incident: {str(e)}",
                        gr.update(visible=False),
                    )
                    return None

            def handle_report_generation(api_key):
                """Generate comprehensive claim report as PDF using AI"""
                if not self.damage_analysis or not self.incident_data:
                    return (
                        "❌ Please complete damage analysis and incident processing first",
                        "<p style='text-align: center; color: gray;'>PDF report will appear here after generation</p>",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                if not api_key.strip():
                    return (
                        "❌ Please enter your Fireworks AI API key first",
                        "<p style='text-align: center; color: gray;'>PDF report will appear here after generation</p>",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                try:
                    # Show processing status
                    yield (
                        "🔄 Generating comprehensive PDF claim report... Please wait",
                        "<p style='text-align: center; color: gray;'>PDF report will appear here after generation</p>",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                    # Generate the PDF report
                    self.final_report_pdf = generate_claim_report_pdf(
                        damage_analysis=self.damage_analysis,
                        incident_data=self.incident_data,
                    )

                    # Extract claim reference for download filename
                    from datetime import datetime

                    timestamp = datetime.now()
                    self.claim_reference = f"CLM-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S')}"

                    # Save PDF to temporary file for viewing and downloading
                    if self.pdf_temp_path and os.path.exists(self.pdf_temp_path):
                        os.remove(self.pdf_temp_path)

                    temp_dir = tempfile.gettempdir()
                    self.pdf_temp_path = os.path.join(
                        temp_dir, f"{self.claim_reference}.pdf"
                    )

                    with open(self.pdf_temp_path, "wb") as f:
                        f.write(self.final_report_pdf)

                    # Create PDF viewer HTML
                    pdf_base64 = base64.b64encode(self.final_report_pdf).decode("utf-8")
                    pdf_viewer_html = f"""
                    <div style="text-align: center; margin: 20px 0;">
                        <h3 style="color: #2563eb;">📋 Insurance Claim Report - {self.claim_reference}</h3>
                        <iframe
                            src="data:application/pdf;base64,{pdf_base64}"
                            width="100%"
                            height="800px"
                            style="border: 2px solid #e5e7eb; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            <p>Your browser does not support PDF viewing.
                            <a href="data:application/pdf;base64,{pdf_base64}" download="{self.claim_reference}.pdf">
                                Click here to download the PDF
                            </a></p>
                        </iframe>
                        <p style="margin-top: 15px; color: #6b7280; font-size: 14px;">
                            📄 Professional PDF report generated successfully! Use the download button below to save.
                        </p>
                    </div>
                    """

                    yield (
                        "✅ Professional PDF claim report generated successfully!",
                        pdf_viewer_html,
                        gr.update(visible=True, value=self.pdf_temp_path),
                        gr.update(visible=True),
                        gr.update(open=True),
                    )
                    return None

                except Exception as e:
                    yield (
                        f"❌ Error generating PDF report: {str(e)}",
                        "<p style='text-align: center; color: red;'>Error generating PDF report</p>",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )
                    return None

            def handle_claim_submission():
                """Handle final claim submission"""
                if not self.final_report_pdf:
                    return "❌ No report available to submit"

                return f"🎉 Claim submitted successfully! Reference: {self.claim_reference}"

            def cleanup_temp_files():
                """Clean up temporary PDF files"""
                if self.pdf_temp_path and os.path.exists(self.pdf_temp_path):
                    try:
                        os.remove(self.pdf_temp_path)
                    except Exception as e:
                        print(f"Error deleting temporary PDF file: {e}")
                        pass

            # Wire up the events
            analyze_btn.click(
                fn=handle_damage_analysis,
                inputs=[image_input, api_key],
                outputs=[damage_status, damage_results],
            )

            # Handle streaming audio for live transcription
            audio_input.stream(
                fn=process_audio_stream,
                inputs=[audio_input, api_key],
                outputs=[transcription_display],
                time_limit=None,
                stream_every=0.5,  # Update every 500ms
                show_progress="hidden",
            )

            process_incident_btn.click(
                fn=handle_incident_processing,
                inputs=[api_key],
                outputs=[incident_status, incident_results],
            )

            generate_report_btn.click(
                fn=handle_report_generation,
                inputs=[api_key],
                outputs=[
                    report_status,
                    pdf_viewer,
                    download_btn,
                    submit_btn,
                    report_accordion,
                ],
            )

            submit_btn.click(fn=handle_claim_submission, outputs=[report_status])

            # Clean up on app close
            demo.load(lambda: None)

        return demo


def create_claims_app():
    """Factory function to create the claims assistant app"""
    app = ClaimsAssistantApp()
    return app.create_interface()


# Create and launch the demo
if __name__ == "__main__":
    print("Starting AI Claims Assistant Demo")
    demo = create_claims_app()
    demo.launch()
