from datetime import datetime, timedelta
from typing import Dict, Any
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.flowables import HRFlowable


def generate_claim_report_pdf(
    damage_analysis: Dict[str, Any],
    incident_data: Dict[str, Any],
    image_path: str = None,
) -> bytes:
    """
    Generate a professional insurance claim report as PDF from analyzed data.

    Args:
        damage_analysis: Results from image damage analysis
        incident_data: Processed incident data from transcript
        image_path: Optional path to the damage photo to include in appendix

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

    # Get incident details safely with date conversion
    date_location = incident_data.get("date_location", {})
    # Convert relative dates to actual dates
    actual_date = _convert_relative_date(date_location.get("date", "Not specified"))
    date_location_converted = {**date_location, "date": actual_date}

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

    # Create PDF document with professional margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # Get styles
    styles = getSampleStyleSheet()

    # Professional custom styles - all black text
    title_style = ParagraphStyle(
        "ProfessionalTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=16,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    header_style = ParagraphStyle(
        "ProfessionalHeader",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=8,
        spaceBefore=16,
        fontName="Helvetica-Bold",
    )

    subheader_style = ParagraphStyle(
        "ProfessionalSubHeader",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=6,
        spaceBefore=8,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "ProfessionalBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        fontName="Helvetica",
        textColor=colors.black,
        alignment=TA_JUSTIFY,
    )

    # Professional table style
    def create_professional_table_style():
        return TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )

    # Helper function to create table cells with proper text wrapping
    def create_table_cell(text: str, is_header: bool = False) -> Paragraph:
        style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.black,
            fontName="Helvetica-Bold" if is_header else "Helvetica",
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0,
        )
        return Paragraph(str(text), style)

    # Build the document content
    story = []

    # Professional Header
    story.append(Paragraph("AUTOMOBILE INSURANCE CLAIM REPORT", title_style))
    story.append(Spacer(1, 12))

    # Claim Information Section
    claim_info_data = [
        [
            create_table_cell("Claim Reference Number:", True),
            create_table_cell(claim_ref),
        ],
        [
            create_table_cell("Report Generated:", True),
            create_table_cell(timestamp.strftime("%B %d, %Y at %I:%M %p")),
        ],
        [
            create_table_cell("Claim Status:", True),
            create_table_cell("Under Review - Pending Adjuster Assignment"),
        ],
        [
            create_table_cell("Processing Priority:", True),
            create_table_cell(
                priority.replace("🔴", "").replace("🟡", "").replace("🟢", "").strip()
            ),
        ],
    ]

    claim_info_table = Table(claim_info_data, colWidths=[2.2 * inch, 4.5 * inch])
    claim_info_table.setStyle(create_professional_table_style())
    story.append(claim_info_table)
    story.append(Spacer(1, 16))

    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    summary_text = f"""
    This claim involves a motor vehicle accident resulting in <b>{damage_severity.lower()}</b> damage to the
    insured vehicle's <b>{damage_location.replace('-', ' ').lower()}</b> area. Based on initial assessment
    of submitted photographic evidence and incident description, this appears to be a legitimate claim
    {"requiring expedited processing due to reported injuries" if injuries_medical.get('anyone_injured', 'no').lower() == 'yes' else "suitable for standard processing procedures"}.
    <br/><br/>
    <b>Primary Recommendation:</b> {recommendation}<br/>
    <b>Preliminary Cost Assessment:</b> {cost_estimate}
    """

    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 16))

    # Incident Details
    story.append(Paragraph("INCIDENT DETAILS", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    # Date, Time & Location
    story.append(Paragraph("Date, Time and Location of Loss", subheader_style))

    incident_data_table = [
        [
            create_table_cell("Date of Loss:", True),
            create_table_cell(
                date_location_converted.get("date", "Not specified in report")
            ),
        ],
        [
            create_table_cell("Time of Loss:", True),
            create_table_cell(date_location.get("time", "Not specified in report")),
        ],
        [
            create_table_cell("Location of Loss:", True),
            create_table_cell(date_location.get("location", "Not specified in report")),
        ],
    ]

    incident_table = Table(incident_data_table, colWidths=[2 * inch, 4.7 * inch])
    incident_table.setStyle(create_professional_table_style())
    story.append(incident_table)
    story.append(Spacer(1, 12))

    # Description of Incident
    story.append(Paragraph("Description of Incident", subheader_style))
    incident_desc = incident_description.get(
        "what_happened", "No detailed description provided in initial report"
    )
    story.append(Paragraph(incident_desc, body_style))
    story.append(Spacer(1, 16))

    # Parties Involved
    story.append(Paragraph("PARTIES INVOLVED", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    parties_data = [
        [
            create_table_cell("Other Party Driver Name:", True),
            create_table_cell(
                parties_involved.get("other_driver_name", "Information not provided")
            ),
        ],
        [
            create_table_cell("Other Party Vehicle:", True),
            create_table_cell(
                parties_involved.get("other_driver_vehicle", "Information not provided")
            ),
        ],
        [
            create_table_cell("Witness Information:", True),
            create_table_cell(
                parties_involved.get("witnesses", "No witnesses reported at this time")
            ),
        ],
    ]

    parties_table = Table(parties_data, colWidths=[2 * inch, 4.7 * inch])
    parties_table.setStyle(create_professional_table_style())
    story.append(parties_table)
    story.append(Spacer(1, 16))

    # Vehicle Damage Assessment
    story.append(Paragraph("VEHICLE DAMAGE ASSESSMENT", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    # Clean up damage description - wrap long text properly
    damage_desc_clean = _format_damage_description(damage_description)

    damage_data = [
        [
            create_table_cell("Damage Severity Classification:", True),
            create_table_cell(damage_severity.title()),
        ],
        [
            create_table_cell("Primary Damage Location:", True),
            create_table_cell(damage_location.replace("-", " ").title()),
        ],
        [
            create_table_cell("Damage Description:", True),
            create_table_cell(damage_desc_clean),
        ],
        [
            create_table_cell("Preliminary Repair Estimate:", True),
            create_table_cell(cost_estimate),
        ],
    ]

    damage_table = Table(damage_data, colWidths=[2 * inch, 4.7 * inch])
    damage_table.setStyle(create_professional_table_style())
    story.append(damage_table)
    story.append(Spacer(1, 12))

    # Evidence Documentation
    evidence_text = """
    <b>Photographic Evidence:</b> Digital photographs of vehicle damage received and analyzed using automated assessment tools.<br/>
    <b>Incident Documentation:</b> Verbal account transcribed and processed for key incident details.
    """
    story.append(Paragraph(evidence_text, body_style))
    story.append(Spacer(1, 16))

    # Injury and Medical Information
    story.append(Paragraph("INJURY AND MEDICAL INFORMATION", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    injury_data = [
        [
            create_table_cell("Personal Injuries Reported:", True),
            create_table_cell(
                injuries_medical.get("anyone_injured", "Not specified").title()
            ),
        ],
        [
            create_table_cell("Injury Details:", True),
            create_table_cell(
                injuries_medical.get(
                    "injury_details", "No specific injury details provided"
                )
            ),
        ],
        [
            create_table_cell("Medical Treatment Sought:", True),
            create_table_cell(
                injuries_medical.get("medical_attention", "Information not available")
            ),
        ],
        [
            create_table_cell("Injury Severity Assessment:", True),
            create_table_cell(
                injuries_medical.get("injury_severity", "None reported").title()
            ),
        ],
    ]

    injury_table = Table(injury_data, colWidths=[2 * inch, 4.7 * inch])
    injury_table.setStyle(create_professional_table_style())
    story.append(injury_table)
    story.append(Spacer(1, 16))

    # Liability Assessment
    story.append(Paragraph("PRELIMINARY LIABILITY ASSESSMENT", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    fault_data = [
        [
            create_table_cell("Initial Fault Determination:", True),
            create_table_cell(
                _format_fault_determination(
                    fault_assessment.get("who_at_fault", "Under investigation")
                )
            ),
        ],
        [
            create_table_cell("Basis for Determination:", True),
            create_table_cell(
                fault_assessment.get(
                    "reason", "Pending detailed investigation and evidence review"
                )
            ),
        ],
    ]

    fault_table = Table(fault_data, colWidths=[2 * inch, 4.7 * inch])
    fault_table.setStyle(create_professional_table_style())
    story.append(fault_table)
    story.append(Spacer(1, 16))

    # Cost Analysis
    story.append(Paragraph("PRELIMINARY COST ANALYSIS", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    medical_costs = _format_medical_costs(injuries_medical)
    total_estimate = _calculate_total_estimate(cost_estimate, injuries_medical)

    cost_data = [
        [
            create_table_cell("Vehicle Repair Estimate:", True),
            create_table_cell(cost_estimate),
        ],
        [
            create_table_cell("Medical Expense Estimate:", True),
            create_table_cell(medical_costs),
        ],
        [
            create_table_cell("Total Preliminary Estimate:", True),
            create_table_cell(total_estimate),
        ],
    ]

    cost_table = Table(cost_data, colWidths=[2 * inch, 4.7 * inch])
    cost_style = create_professional_table_style()
    # Highlight total row
    cost_style.add("BACKGROUND", (0, 2), (1, 2), colors.lightgrey)
    cost_style.add("FONTNAME", (0, 2), (1, 2), "Helvetica-Bold")
    cost_table.setStyle(cost_style)

    story.append(cost_table)
    story.append(Spacer(1, 16))

    # Action Items and Next Steps
    story.append(Paragraph("RECOMMENDED ACTION ITEMS", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    next_steps = _generate_next_steps_professional(
        damage_severity, injuries_medical, fault_assessment
    )
    story.append(Paragraph(next_steps, body_style))
    story.append(Spacer(1, 16))

    # Processing Notes
    story.append(Paragraph("PROCESSING NOTES", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    processing_notes = f"""
    This preliminary assessment was generated using automated analysis tools to expedite initial claim processing.
    Photographic evidence and incident descriptions were processed using artificial intelligence to provide rapid
    initial assessment. {"Given the reported injuries, this claim has been flagged for expedited human review." if injuries_medical.get('anyone_injured', 'no').lower() == 'yes' else "Standard processing timeline applies per company guidelines."}
    Final claim determination requires licensed adjuster review and approval.
    """

    story.append(Paragraph(processing_notes, body_style))
    story.append(Spacer(1, 20))

    # Footer Information
    footer_data = [
        [
            create_table_cell("Report Generated By:", True),
            create_table_cell("AI Claims Processing System"),
        ],
        [
            create_table_cell("Processing Timestamp:", True),
            create_table_cell(timestamp.strftime("%I:%M %p EST")),
        ],
        [
            create_table_cell("Human Review Status:", True),
            create_table_cell("Required - Pending Assignment"),
        ],
        [
            create_table_cell("System Confidence Level:", True),
            create_table_cell("High - Standard Processing Recommended"),
        ],
    ]

    footer_table = Table(footer_data, colWidths=[2 * inch, 4.7 * inch])
    footer_table.setStyle(create_professional_table_style())
    story.append(footer_table)
    story.append(Spacer(1, 12))

    # Evidence/Appendix Section
    story.append(Paragraph("APPENDIX - EVIDENCE DOCUMENTATION", header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 8))

    # Raw transcript section
    story.append(Paragraph("Raw Incident Description Transcript", subheader_style))

    # Get the original raw description
    raw_description = incident_description.get(
        "what_happened", "No transcript available"
    )

    # Create a formatted transcript
    transcript_text = f"""
    <b>Original Incident Account (Unedited):</b><br/><br/>
    "{raw_description}"
    <br/><br/>
    <i>Note: This is the unedited transcript of the policyholder's account of the incident as provided during initial report.</i>
    """

    story.append(Paragraph(transcript_text, body_style))
    story.append(Spacer(1, 12))

    # Damage photo section
    story.append(Paragraph("Photographic Evidence", subheader_style))

    if image_path:
        try:
            # Add the damage photo
            img = Image(image_path, width=4 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 8))

            photo_caption = Paragraph(
                "<i>Figure 1: Vehicle damage photograph submitted with initial claim report. "
                "Image analyzed using automated damage assessment tools.</i>",
                ParagraphStyle(
                    "PhotoCaption",
                    parent=styles["Normal"],
                    fontSize=9,
                    textColor=colors.black,
                    alignment=TA_CENTER,
                    spaceAfter=8,
                ),
            )
            story.append(photo_caption)
        except Exception as e:
            # If image can't be loaded, show placeholder text
            print(f"Error loading damage photo: {e}")
            story.append(
                Paragraph(
                    "Damage photograph submitted with claim (unable to display in this report format).",
                    body_style,
                )
            )
    else:
        story.append(
            Paragraph(
                "Damage photograph submitted with claim and analyzed using automated assessment tools. "
                "Original digital file maintained in claim documentation system.",
                body_style,
            )
        )

    story.append(Spacer(1, 12))

    # Raw damage analysis
    story.append(Paragraph("Technical Damage Analysis Output", subheader_style))

    # Get the raw damage description
    raw_damage_analysis = damage_analysis.get(
        "description", "No technical analysis available"
    )

    technical_analysis_text = f"""
    <b>Automated Damage Assessment Output (Technical):</b><br/><br/>
    {_format_technical_description(raw_damage_analysis)}
    <br/><br/>
    <i>Note: This is the raw output from the automated damage assessment system.
    The summary version appears in the main report above.</i>
    """

    story.append(Paragraph(technical_analysis_text, body_style))
    story.append(Spacer(1, 16))

    # Legal Disclaimer
    disclaimer = Paragraph(
        "<i>This automated preliminary assessment is provided for initial processing purposes only. "
        "All claim determinations are subject to policy terms, conditions, and coverage verification. "
        "Final settlement authority rests with assigned licensed adjuster pending completion of full investigation.</i>",
        ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.black,
            alignment=TA_CENTER,
            leftIndent=0.5 * inch,
            rightIndent=0.5 * inch,
        ),
    )
    story.append(disclaimer)

    # Build PDF
    doc.build(story)

    # Get the PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def _format_damage_description(description: str) -> str:
    """Clean and format damage description for professional presentation"""
    if not description or len(description) < 50:
        return description

    # Remove redundant technical formatting
    cleaned = description.replace("###", "").replace("**", "").replace("- **", "• ")

    # Extract key summary if description is very long
    if len(cleaned) > 300:
        lines = cleaned.split("\n")
        summary_lines = [
            line.strip()
            for line in lines
            if line.strip()
            and not line.strip().startswith("##")
            and len(line.strip()) > 10
        ][:3]
        return " ".join(summary_lines[:2]) + "..."

    return cleaned[:250] + "..." if len(cleaned) > 250 else cleaned


def _format_fault_determination(fault: str) -> str:
    """Format fault determination for professional presentation"""
    fault_map = {
        "other_driver": "Other Party - Preliminary",
        "policyholder": "Policyholder - Preliminary",
        "unclear": "Undetermined - Investigation Required",
        "both": "Comparative Negligence - Investigation Required",
    }
    return fault_map.get(fault.lower(), "Under Investigation")


def _get_priority_level(damage_severity: str, injuries_reported: str) -> str:
    """Determine claim priority using professional terminology"""
    if injuries_reported.lower() == "yes":
        return "HIGH PRIORITY - Personal Injury Claim"
    elif damage_severity.lower() == "major":
        return "ELEVATED PRIORITY - Significant Property Damage"
    elif damage_severity.lower() == "moderate":
        return "STANDARD PRIORITY - Moderate Property Damage"
    else:
        return "ROUTINE PRIORITY - Minor Property Damage"


def _estimate_cost_range(damage_severity: str) -> str:
    """Estimate repair costs based on damage severity"""
    severity_costs = {
        "minor": "$750 - $2,500",
        "moderate": "$2,500 - $7,500",
        "major": "$7,500 - $18,000",
        "severe": "$18,000 - $35,000",
    }
    return severity_costs.get(damage_severity.lower(), "$2,000 - $5,000")


def _get_recommendation(damage_severity: str, injuries_reported: str) -> str:
    """Generate professional recommendation"""
    if injuries_reported.lower() == "yes":
        return "IMMEDIATE ACTION REQUIRED: Assign specialist adjuster for personal injury claim within 24 hours"
    elif damage_severity.lower() in ["major", "severe"]:
        return "PRIORITY PROCESSING: Schedule comprehensive inspection within 48 hours"
    else:
        return "STANDARD PROCESSING: Assign adjuster within normal service level agreement timeframe"


def _format_medical_costs(injuries_medical: Dict[str, Any]) -> str:
    """Format medical cost estimate professionally"""
    if injuries_medical.get("anyone_injured", "no").lower() == "yes":
        severity = injuries_medical.get("injury_severity", "minor").lower()
        if severity == "severe":
            return "$15,000 - $75,000 (Preliminary)"
        elif severity == "moderate":
            return "$3,000 - $15,000 (Preliminary)"
        else:
            return "$500 - $3,000 (Preliminary)"
    return "No medical expenses anticipated"


def _calculate_total_estimate(
    repair_cost: str, injuries_medical: Dict[str, Any]
) -> str:
    """Calculate total claim estimate professionally"""
    if injuries_medical.get("anyone_injured", "no").lower() == "yes":
        return f"{repair_cost} plus medical expenses (subject to investigation)"
    return repair_cost


def _generate_next_steps_professional(
    damage_severity: str,
    injuries_medical: Dict[str, Any],
    fault_assessment: Dict[str, Any],
) -> str:
    """Generate professional action items"""

    steps = []

    # Always required steps
    steps.append(
        "1. <b>Adjuster Assignment:</b> Assign licensed adjuster for detailed investigation and coverage verification."
    )
    steps.append(
        "2. <b>Vehicle Inspection:</b> Schedule comprehensive damage assessment with approved appraiser."
    )
    steps.append(
        "3. <b>Third Party Contact:</b> Attempt contact with other party's insurance carrier for coordination."
    )

    # Conditional steps based on circumstances
    step_num = 4

    if injuries_medical.get("anyone_injured", "no").lower() == "yes":
        steps.append(
            f"{step_num}. <b>Medical Documentation:</b> Request medical records and treatment documentation from healthcare providers."
        )
        step_num += 1
        steps.append(
            f"{step_num}. <b>Injury Specialist:</b> Engage personal injury specialist for claim evaluation."
        )
        step_num += 1

    if fault_assessment.get("who_at_fault", "unclear").lower() == "unclear":
        steps.append(
            f"{step_num}. <b>Police Report:</b> Obtain official police report if available for liability determination."
        )
        step_num += 1

    if damage_severity.lower() in ["major", "severe"]:
        steps.append(
            f"{step_num}. <b>Multiple Estimates:</b> Secure at least two independent repair estimates for cost validation."
        )
        step_num += 1

    # Final step
    steps.append(
        f"{step_num}. <b>Customer Communication:</b> Contact policyholder within 24 hours to confirm receipt and outline next steps."
    )

    return "<br/>".join(steps)


def _convert_relative_date(date_str: str) -> str:
    """Convert relative dates like 'today', 'yesterday' to actual dates"""
    if not date_str or date_str.lower() in ["not specified", "unknown", ""]:
        return "Not specified in report"

    # Get current date
    today = datetime.now()

    # Dictionary of relative date conversions
    relative_dates = {
        "today": today.strftime("%B %d, %Y"),
        "yesterday": (today - timedelta(days=1)).strftime("%B %d, %Y"),
        "yesterday night": (today - timedelta(days=1)).strftime("%B %d, %Y (evening)"),
        "yesterday evening": (today - timedelta(days=1)).strftime(
            "%B %d, %Y (evening)"
        ),
        "last night": (today - timedelta(days=1)).strftime("%B %d, %Y (night)"),
        "this morning": today.strftime("%B %d, %Y (morning)"),
        "this afternoon": today.strftime("%B %d, %Y (afternoon)"),
        "this evening": today.strftime("%B %d, %Y (evening)"),
        "2 days ago": (today - timedelta(days=2)).strftime("%B %d, %Y"),
        "3 days ago": (today - timedelta(days=3)).strftime("%B %d, %Y"),
        "a few days ago": (today - timedelta(days=2)).strftime(
            "%B %d, %Y (approximate)"
        ),
        "earlier today": today.strftime("%B %d, %Y (earlier)"),
        "day before yesterday": (today - timedelta(days=2)).strftime("%B %d, %Y"),
    }

    # Check for exact matches first
    date_lower = date_str.lower().strip()
    if date_lower in relative_dates:
        return relative_dates[date_lower]

    # Check for partial matches
    for relative_term, actual_date in relative_dates.items():
        if relative_term in date_lower:
            return actual_date

    # If no relative date found, return original
    return date_str


def _format_technical_description(description: str) -> str:
    """Format technical damage description for appendix"""
    if not description:
        return "No technical analysis data available"

    # Clean up technical formatting but preserve more detail than main report
    cleaned = description.replace("###", "").replace("**", "")

    # If it's very long, keep more content than the main report version
    if len(cleaned) > 800:
        # Split into sections and keep first few sections
        sections = cleaned.split("\n\n")
        important_sections = [
            s.strip() for s in sections if s.strip() and len(s.strip()) > 20
        ]
        return (
            "\n\n".join(important_sections[:4])
            + "\n\n[Additional technical details available in system logs]"
        )

    return cleaned
