from pathlib import Path
import gradio as gr
import threading
import time

from modules.image_analysis import pil_to_base64_dict, analyze_damage_image
from modules.transcription import transcribe_audio_with_fireworks

_FILE_PATH = Path(__file__).parents[1]


class ClaimsAssistantApp:
    def __init__(self):
        self.damage_analysis = None
        self.incident_data = None
        self.live_transcription = ""
        self.transcription_lock = threading.Lock()

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
                    **Step 2:** Describe incident (record audio)
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

                    # Step 2: Incident Description
                    gr.Markdown("## 🎤 Step 2: Describe the Incident 🎤")

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Record Audio")
                            audio_input = gr.Audio(
                                label="Record Incident Description",
                                type="filepath",
                                sources=["microphone"],
                            )
                        with gr.Column():
                            gr.Markdown("### Live Transcription")
                            transcription_display = gr.Textbox(
                                label="Live Transcription",
                                placeholder="Audio transcription will appear here as you speak...",
                                lines=6,
                                interactive=False,
                            )

                    process_incident_btn = gr.Button(
                        "📝 Process Incident", variant="primary"
                    )

                    incident_status = gr.Textbox(
                        label="Processing Status",
                        value="Ready to process incident",
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

                    # Final Report Display
                    with gr.Accordion(
                        "📋 Generated Claim Report", open=False
                    ) as report_accordion:
                        final_report = gr.Markdown(
                            value="*Report will appear here after generation*",
                            label="Claim Report",
                        )

                        with gr.Row():
                            download_btn = gr.DownloadButton(
                                "💾 Download Report", visible=False
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

                except Exception as e:
                    yield (
                        f"❌ Error analyzing damage: {str(e)}",
                        gr.update(visible=False),
                    )

            def live_transcription_callback(text):
                """Callback for live transcription updates"""
                with self.transcription_lock:
                    self.live_transcription = text

            def update_transcription_display():
                """Periodically update the transcription display"""
                with self.transcription_lock:
                    return self.live_transcription

            def handle_incident_processing(audio, api_key):
                if audio is None:
                    return (
                        "❌ Please record audio first",
                        gr.update(visible=False),
                        "No audio recorded",
                    )

                if not api_key.strip():
                    return (
                        "❌ Please enter your Fireworks AI API key first",
                        gr.update(visible=False),
                        "API key required",
                    )

                try:
                    # Update status
                    yield (
                        "🔄 Transcribing audio... Please wait",
                        gr.update(visible=False),
                        "Processing audio...",
                    )

                    # Transcribe audio using Fireworks
                    final_transcription = transcribe_audio_with_fireworks(
                        audio_file_path=audio,
                        api_key=api_key,
                        live_callback=live_transcription_callback,
                    )

                    # TODO: Process the transcription to extract structured incident data
                    # For now, we'll create a placeholder structure
                    self.incident_data = {
                        "transcription": final_transcription,
                        "incident_type": "collision",  # Could be extracted from transcription
                        "date": "2024-03-12",  # Could be extracted from transcription
                        "location": "Main Street intersection",  # Could be extracted
                        "parties_involved": 2,  # Could be counted from transcription
                        "fault_assessment": "pending",
                        "weather_conditions": "clear",  # Could be extracted
                        "injuries_reported": False,  # Could be extracted
                        "vehicle_description": "Sedan",  # Could be extracted
                    }

                    yield (
                        "✅ Incident processing completed successfully!",
                        gr.update(value=self.incident_data, visible=True),
                        final_transcription,
                    )
                    return None

                except Exception as e:
                    yield (
                        f"❌ Error processing incident: {str(e)}",
                        gr.update(visible=False),
                        "Error processing audio",
                    )
                    return None

            def handle_report_generation(api_key):
                if not self.damage_analysis or not self.incident_data:
                    return (
                        "❌ Please complete damage analysis and incident processing first",
                        "Report will appear here after generation",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                if not api_key.strip():
                    return (
                        "❌ Please enter your Fireworks AI API key first",
                        "Report will appear here after generation",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                try:
                    # TODO: Use Fireworks to generate a comprehensive report
                    # For now, create a detailed sample report
                    transcription = self.incident_data.get("transcription", "N/A")

                    report = f"""
                            # Insurance Claim Report

                            **Claim Reference**: CLM-2024-{int(time.time())}-001
                            **Date Generated**: {time.strftime("%Y-%m-%d %H:%M:%S")}

                            ---

                            ## 🚗 Damage Analysis Summary

                            - **Damage Type**: {self.damage_analysis.get('damage_type', 'N/A')}
                            - **Severity Level**: {self.damage_analysis.get('severity', 'N/A')}
                            - **Affected Areas**: {self.damage_analysis.get('affected_parts', 'N/A')}
                            - **Estimated Repair Cost**: {self.damage_analysis.get('estimated_cost', 'N/A')}
                            - **Additional Notes**: {self.damage_analysis.get('description', 'N/A')}

                            ---

                            ## 📝 Incident Summary

                            - **Incident Date**: {self.incident_data.get('date', 'N/A')}
                            - **Location**: {self.incident_data.get('location', 'N/A')}
                            - **Incident Type**: {self.incident_data.get('incident_type', 'N/A')}
                            - **Parties Involved**: {self.incident_data.get('parties_involved', 'N/A')}
                            - **Weather Conditions**: {self.incident_data.get('weather_conditions', 'N/A')}
                            - **Injuries Reported**: {"Yes" if self.incident_data.get('injuries_reported') else "No"}

                            ### Incident Description (Transcribed)
                            *"{transcription[:500]}{'...' if len(transcription) > 500 else ''}"*

                            ---

                            ## 🔍 Assessment & Recommendations

                            Based on the automated analysis of the damage photos and incident description:

                            1. **Damage Assessment**: The vehicle shows {self.damage_analysis.get('severity', 'moderate')} damage
                            2. **Claim Validity**: Initial assessment suggests this is a legitimate claim
                            3. **Next Steps**:
                               - Physical inspection recommended
                               - Obtain additional documentation if needed
                               - Process for repair authorization

                            **Adjuster Notes**: This claim has been processed using AI assistance and requires human review for final approval.

                            ---

                            *This report was generated automatically using Fireworks AI technology*`
                    """

                    return (
                        "✅ Claim report generated successfully!",
                        report,
                        gr.update(visible=True),
                        gr.update(visible=True),
                        gr.update(open=True),
                    )
                except Exception as e:
                    return (
                        f"❌ Error generating report: {str(e)}",
                        "Report will appear here after generation",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

            def handle_claim_submission():
                claim_ref = f"CLM-2024-{int(time.time())}-001"
                return f"🎉 Claim submitted successfully! Reference #: {claim_ref}"

            # Wire up the events
            analyze_btn.click(
                fn=handle_damage_analysis,
                inputs=[image_input, api_key],
                outputs=[damage_status, damage_results],
            )

            process_incident_btn.click(
                fn=handle_incident_processing,
                inputs=[audio_input, api_key],
                outputs=[
                    incident_status,
                    incident_results,
                    transcription_display,
                ],
            )

            generate_report_btn.click(
                fn=handle_report_generation,
                inputs=[api_key],
                outputs=[
                    report_status,
                    final_report,
                    download_btn,
                    submit_btn,
                    report_accordion,
                ],
            )

            submit_btn.click(fn=handle_claim_submission, outputs=[report_status])

            # Set up periodic updates for live transcription
            # Note: This is a simplified approach - in production you'd want more sophisticated real-time updates
            demo.load(
                fn=update_transcription_display,
                inputs=[],
                outputs=[transcription_display],
            )

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
