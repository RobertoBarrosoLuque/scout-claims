from pathlib import Path

import gradio as gr

_FILE_PATH = Path(__file__).parents[1]


class ClaimsAssistantApp:
    def __init__(self):
        self.damage_analysis = None
        self.incident_data = None

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
                    **Step 2:** Record incident description
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
                    gr.Markdown("## 🎤 Step 2: Record Incident Description 🎤")

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
                        gr.update(visible=False),
                    )

                self.damage_analysis = analyze_damage_image(image, api_key)

                if "error" in self.damage_analysis:
                    return (
                        f"❌ Error: {self.damage_analysis['error']}",
                        gr.update(visible=False),
                        gr.update(visible=False),
                    )

                return (
                    "✅ Damage analysis completed successfully!",
                    gr.update(value=self.damage_analysis, visible=True),
                    gr.update(visible=True),
                )

            def handle_incident_processing(audio, api_key):
                if audio is None:
                    return (
                        "❌ Please record audio first",
                        gr.update(visible=False),
                        "No audio recorded",
                        gr.update(visible=False),
                    )

                self.incident_data = process_incident_description(None, audio, api_key)

                if "error" in self.incident_data:
                    return (
                        f"❌ Error: {self.incident_data['error']}",
                        gr.update(visible=False),
                        "Error processing audio",
                        gr.update(visible=False),
                    )

                # Extract transcription from incident data for display
                transcription_text = self.incident_data.get(
                    "transcription", "Audio transcribed successfully"
                )

                return (
                    "✅ Incident processing completed successfully!",
                    gr.update(value=self.incident_data, visible=True),
                    transcription_text,
                    gr.update(visible=True),
                )

            def handle_report_generation(api_key):
                if not self.damage_analysis or not self.incident_data:
                    return (
                        "❌ Please complete damage analysis and incident processing first",
                        "Report will appear here after generation",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                report = generate_claim_report(
                    self.damage_analysis, self.incident_data, api_key
                )

                if report.startswith("Error:"):
                    return (
                        report,
                        "Report will appear here after generation",
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(open=False),
                    )

                return (
                    "✅ Claim report generated successfully!",
                    report,
                    gr.update(visible=True),
                    gr.update(visible=True),
                    gr.update(open=True),
                )

            def handle_claim_submission():
                return "🎉 Claim submitted successfully! Reference #: CLM-2024-0312-001"

            # Wire up the events
            analyze_btn.click(
                fn=handle_damage_analysis,
                inputs=[image_input, api_key],
                outputs=[damage_status, damage_results, damage_results],
            )

            process_incident_btn.click(
                fn=handle_incident_processing,
                inputs=[audio_input, api_key],
                outputs=[
                    incident_status,
                    incident_results,
                    transcription_display,
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
