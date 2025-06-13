from datetime import datetime
from typing import Dict, Any
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.flowables import HRFlowable


def generate_claim_report_pdf(
    damage_analysis: Dict[str, Any], incident_data: Dict[str, Any]
) -> bytes:
    """
    Generate a comprehensive insurance claim report as PDF from analyzed data.

    Args:
        damage_analysis: Results from image damage analysis
        incident_data: Processed incident data from transcript

    Returns:
        PDF bytes for the formatted claim report
    """

    # Create a BytesIO buffer to hold the PDF
    buffer = io.BytesIO()

    # Generate claim reference number
    timestamp = datetime.now()
    claim_ref = f"CLM-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S')}"

    # Extract key information safely
    damage_description = damage_analysis.get("description", "Vehicle damage detected")
    damage_severity = damage_analysis.get("severity", "moderate")
    damage_location = damage_analysis.get("location", "unknown")

    # Get incident details safely
    date_location = incident_data.get("date_location", {})
    parties_involved = incident_data.get("parties_involved", {})
    fault_assessment = incident_data.get("fault_assessment", {})
    incident_description = incident_data.get("incident_description", {})
    injuries_medical = incident_data.get("injuries_medical", {})

    # Generate assessments
    priority = _get_priority_level(
        damage_severity, injuries_medical.get("anyone_injured", "no")
    )
    cost_estimate = _estimate_cost_range(damage_severity)
    recommendation = _get_recommendation(
        damage_severity, injuries_medical.get("anyone_injured", "no")
    )

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Get styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.darkblue,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    header_style = ParagraphStyle(
        "CustomHeader",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=12,
        spaceBefore=12,
        fontName="Helvetica-Bold",
    )

    subheader_style = ParagraphStyle(
        "CustomSubHeader",
        parent=styles["Heading3"],
        fontSize=14,
        textColor=colors.blue,
        spaceAfter=8,
        spaceBefore=8,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
        fontName="Helvetica",
    )

    # Build the document content
    story = []

    # Header with logo area and title
    story.append(Paragraph("🚗 INSURANCE CLAIM REPORT 🚗", title_style))
    story.append(Spacer(1, 20))

    # Claim info table
    claim_info_data = [
        ["Claim Reference:", claim_ref],
        ["Date Generated:", timestamp.strftime("%B %d, %Y at %I:%M %p")],
        ["Status:", "Under Review"],
        [
            "Priority:",
            priority.replace("🔴", "").replace("🟡", "").replace("🟢", "").strip(),
        ],
    ]

    claim_info_table = Table(claim_info_data, colWidths=[2 * inch, 4 * inch])
    claim_info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(claim_info_table)
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    summary_text = f"""
    Vehicle sustained <b>{damage_severity}</b> damage to the <b>{damage_location.replace('-', ' ')}</b> area.
    Initial assessment indicates this is a legitimate claim requiring {"immediate attention" if priority.startswith("HIGH") else "standard processing"}.
    <br/><br/>
    <b>Recommendation:</b> {recommendation}<br/>
    <b>Estimated Repair Cost:</b> {cost_estimate}
    """

    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 15))

    # Accident Details
    story.append(Paragraph("ACCIDENT DETAILS", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    # Date, Time & Location
    story.append(Paragraph("Date, Time & Location", subheader_style))

    accident_data = [
        ["Date:", date_location.get("date", "Not specified")],
        ["Time:", date_location.get("time", "Not specified")],
        ["Location:", date_location.get("location", "Not specified")],
    ]

    accident_table = Table(accident_data, colWidths=[1.5 * inch, 4.5 * inch])
    accident_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(accident_table)
    story.append(Spacer(1, 10))

    # How It Happened
    story.append(Paragraph("How It Happened", subheader_style))
    story.append(
        Paragraph(
            incident_description.get("what_happened", "No description provided"),
            body_style,
        )
    )
    story.append(Spacer(1, 15))

    # Parties Involved
    story.append(Paragraph("PARTIES INVOLVED", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    parties_data = [
        [
            "Other Driver Name:",
            parties_involved.get("other_driver_name", "Not specified"),
        ],
        [
            "Other Driver Vehicle:",
            parties_involved.get("other_driver_vehicle", "Not specified"),
        ],
        ["Witnesses:", parties_involved.get("witnesses", "None reported")],
    ]

    parties_table = Table(parties_data, colWidths=[2 * inch, 4 * inch])
    parties_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgreen),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(parties_table)
    story.append(Spacer(1, 15))

    # Vehicle Damage
    story.append(Paragraph("VEHICLE DAMAGE", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    damage_data = [
        ["Severity:", damage_severity.title()],
        ["Location:", damage_location.replace("-", " ").title()],
        ["Description:", damage_description],
        ["Estimated Cost:", cost_estimate],
    ]

    damage_table = Table(damage_data, colWidths=[2 * inch, 4 * inch])
    damage_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightyellow),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(damage_table)
    story.append(Spacer(1, 10))

    # Evidence
    evidence_text = """
    <b>✓ Damage Photos:</b> Received and analyzed<br/>
    <b>✓ Incident Recording:</b> Transcribed and processed
    """
    story.append(Paragraph(evidence_text, body_style))
    story.append(Spacer(1, 15))

    # Injuries & Medical
    story.append(Paragraph("INJURIES & MEDICAL", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    injury_data = [
        ["Anyone Injured:", injuries_medical.get("anyone_injured", "Unknown").title()],
        ["Injury Details:", injuries_medical.get("injury_details", "None reported")],
        [
            "Medical Attention:",
            injuries_medical.get("medical_attention", "Not specified"),
        ],
        ["Injury Severity:", injuries_medical.get("injury_severity", "None").title()],
    ]

    injury_table = Table(injury_data, colWidths=[2 * inch, 4 * inch])
    injury_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightpink),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(injury_table)
    story.append(Spacer(1, 15))

    # Fault Determination
    story.append(Paragraph("FAULT DETERMINATION", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    fault_data = [
        [
            "Who's At Fault:",
            fault_assessment.get("who_at_fault", "Under investigation").title(),
        ],
        ["Reason:", fault_assessment.get("reason", "Investigation required")],
    ]

    fault_table = Table(fault_data, colWidths=[2 * inch, 4 * inch])
    fault_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightcyan),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(fault_table)
    story.append(Spacer(1, 15))

    # Estimated Costs
    story.append(Paragraph("ESTIMATED COSTS", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    medical_costs = _format_medical_costs(injuries_medical)
    total_estimate = _calculate_total_estimate(cost_estimate, injuries_medical)

    cost_data = [
        ["Vehicle Repair:", cost_estimate],
        ["Medical Expenses:", medical_costs],
        ["Total Estimated:", total_estimate],
    ]

    cost_table = Table(cost_data, colWidths=[2 * inch, 4 * inch])
    cost_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("BACKGROUND", (0, 2), (1, 2), colors.yellow),  # Highlight total
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (0, 2), (1, 2), "Helvetica-Bold"),  # Bold total
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(cost_table)
    story.append(Spacer(1, 15))

    # Next Steps
    story.append(Paragraph("NEXT STEPS", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    next_steps = _generate_next_steps(
        damage_severity, injuries_medical, fault_assessment
    )
    # Convert numbered list to paragraph format
    steps_formatted = next_steps.replace("\n", "<br/>")
    story.append(Paragraph(steps_formatted, body_style))
    story.append(Spacer(1, 15))

    # Adjuster Notes
    story.append(Paragraph("ADJUSTER NOTES", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.darkblue))

    notes_text = f"""
    • Claim processed using AI-assisted analysis<br/>
    • Photos and incident description analyzed automatically<br/>
    • {"High priority due to injuries - expedite processing" if injuries_medical.get('anyone_injured', 'no').lower() == 'yes' else "Standard processing timeline applies"}<br/>
    • Human adjuster review required for final approval
    """

    story.append(Paragraph(notes_text, body_style))
    story.append(Spacer(1, 20))

    # Footer
    footer_data = [
        ["Generated by:", "Scout AI Claims Assistant"],
        ["Processing Time:", timestamp.strftime("%I:%M %p")],
        ["Review Required:", "Yes"],
    ]

    footer_table = Table(footer_data, colWidths=[2 * inch, 4 * inch])
    footer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )

    story.append(footer_table)
    story.append(Spacer(1, 10))

    disclaimer = Paragraph(
        "<i>This preliminary assessment is based on automated analysis of submitted photos and incident description. Final determination pending adjuster review.</i>",
        ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        ),
    )
    story.append(disclaimer)

    # Build PDF
    doc.build(story)

    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def _get_priority_level(damage_severity: str, injuries_reported: str) -> str:
    """Determine claim priority"""
    if injuries_reported.lower() == "yes":
        return "HIGH - Injuries Reported"
    elif damage_severity.lower() == "major":
        return "HIGH - Major Damage"
    elif damage_severity.lower() == "moderate":
        return "MEDIUM - Moderate Damage"
    else:
        return "STANDARD - Minor Damage"


def _estimate_cost_range(damage_severity: str) -> str:
    """Estimate repair costs based on damage severity"""
    severity_costs = {
        "minor": "$500 - $1,500",
        "moderate": "$1,500 - $5,000",
        "major": "$5,000 - $15,000",
        "severe": "$15,000+",
    }
    return severity_costs.get(damage_severity.lower(), "$1,000 - $3,000")


def _get_recommendation(damage_severity: str, injuries_reported: str) -> str:
    """Generate simple recommendation"""
    if injuries_reported.lower() == "yes":
        return "URGENT: Expedite processing due to injuries"
    elif damage_severity.lower() in ["major", "severe"]:
        return "PRIORITY: Schedule inspection within 48 hours"
    else:
        return "STANDARD: Process within normal timeline"


def _format_medical_costs(injuries_medical: Dict[str, Any]) -> str:
    """Format medical cost estimate"""
    if injuries_medical.get("anyone_injured", "no").lower() == "yes":
        severity = injuries_medical.get("injury_severity", "minor").lower()
        if severity == "severe":
            return "$10,000 - $50,000"
        elif severity == "moderate":
            return "$2,000 - $10,000"
        else:
            return "$500 - $2,000"
    return "$0 - No injuries reported"


def _calculate_total_estimate(
    repair_cost: str, injuries_medical: Dict[str, Any]
) -> str:
    """Calculate total claim estimate"""
    if injuries_medical.get("anyone_injured", "no").lower() == "yes":
        return f"{repair_cost} + medical costs"
    return repair_cost


def _generate_next_steps(
    damage_severity: str,
    injuries_medical: Dict[str, Any],
    fault_assessment: Dict[str, Any],
) -> str:
    """Generate actionable next steps"""
    steps = [
        "1. Schedule vehicle inspection - Verify damage assessment",
        "2. Contact other party - Obtain insurance information",
    ]

    # Conditional steps
    if injuries_medical.get("anyone_injured", "no").lower() == "yes":
        steps.append("3. Request medical records - Document injury claims")
        steps.append("4. Coordinate medical provider - Ensure proper treatment")

    if fault_assessment.get("who_at_fault", "unclear") == "unclear":
        steps.append("3. Obtain police report - Clarify fault determination")

    if damage_severity.lower() in ["major", "severe"]:
        steps.append(
            "4. Get multiple repair estimates - Ensure accurate cost assessment"
        )

    steps.append(
        f"{len(steps) + 1}. Update customer - Communicate timeline and next steps"
    )

    return "\n".join(steps)
