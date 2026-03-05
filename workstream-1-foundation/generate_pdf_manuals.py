#!/usr/bin/env python3
"""
Generate mock PDF technical manuals for Main Character Energy
- vestas_v150_repair_manual.pdf
- ge_7ha_gas_turbine_manual.pdf
- abb_substation_manual.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

OUTPUT_DIR = "/Users/pravin.varma/Documents/Demo/main-character-energy/workstream-1-foundation/mock_data"

def create_manual_header(title, subtitle, model):
    """Create consistent manual header"""
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1B3139'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    return [
        Paragraph(title, title_style),
        Paragraph(subtitle, subtitle_style),
        Paragraph(f"<b>Model:</b> {model}", styles['Normal']),
        Spacer(1, 0.5*cm)
    ]

def create_vestas_manual():
    """Generate Vestas V150 Wind Turbine Repair Manual"""
    filename = os.path.join(OUTPUT_DIR, "vestas_v150_repair_manual.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.extend(create_manual_header(
        "Vestas V150-4.2MW",
        "Technical Repair Manual",
        "V150-4.2MW with GridStreamer Converter"
    ))

    # Section 1: Safety
    story.append(Paragraph("<b>1. SAFETY WARNINGS</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("⚠️ HIGH VOLTAGE - De-energize turbine before maintenance", styles['Normal']))
    story.append(Paragraph("⚠️ ROTATING PARTS - Lock out rotor before entry", styles['Normal']))
    story.append(Paragraph("⚠️ FALL HAZARD - Use certified harness at all times", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Section 2: Vibration Bearing Replacement
    story.append(Paragraph("<b>2. VIBRATION BEARING REPLACEMENT PROCEDURE</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>2.1 Diagnostic Criteria</b>", styles['Heading3']))
    story.append(Paragraph("Replace main shaft bearings if:", styles['Normal']))
    story.append(Paragraph("• Vibration exceeds 80 Hz for more than 24 hours", styles['Normal']))
    story.append(Paragraph("• Temperature exceeds 85°C at bearing housing", styles['Normal']))
    story.append(Paragraph("• Unusual noise or grinding detected during rotation", styles['Normal']))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>2.2 Required Parts</b>", styles['Heading3']))
    parts_data = [
        ['Part Number', 'Description', 'Quantity'],
        ['SKF-7320-BECBM', 'Main Shaft Bearing Kit', '2'],
        ['GREASE-EP2-5KG', 'Lithium EP2 Grease Cartridge', '3'],
        ['TORQUE-500NM', 'Torque Wrench Set (50-500 Nm)', '1'],
        ['SEAL-MS150', 'Main Shaft Seal', '2']
    ]

    parts_table = Table(parts_data)
    parts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B3139')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(parts_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>2.3 Step-by-Step Procedure</b>", styles['Heading3']))
    steps = [
        "De-energize turbine and lock out main breaker (LOTO procedure MCE-WT-001)",
        "Apply rotor lock and confirm zero rotation",
        "Remove nacelle access panels (bolts: M12 x 40mm, torque: 50 Nm)",
        "Disconnect vibration sensor cables (marked with RED tags)",
        "Remove bearing housing cover (12 bolts, torque sequence: star pattern)",
        "Extract old bearing using hydraulic puller (pressure: 150 bar max)",
        "Clean bearing seat with isopropyl alcohol and lint-free cloth",
        "Apply thin layer of EP2 grease to bearing seat",
        "Install new SKF-7320 bearing (press fit, max force: 25 kN)",
        "Install new shaft seal with seal driver tool",
        "Fill bearing cavity with EP2 grease (approximately 800g)",
        "Reassemble housing cover (torque: 120 Nm, star pattern)",
        "Reconnect vibration sensors and verify signal output",
        "Remove rotor lock and perform manual rotation test",
        "Re-energize turbine and monitor vibration for 24 hours",
        "Record baseline vibration reading in maintenance log"
    ]

    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"<b>Step {i}:</b> {step}", styles['Normal']))
        story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("<b>Estimated Duration:</b> 6-8 hours (2 technicians)", styles['Normal']))
    story.append(Paragraph("<b>Post-Maintenance:</b> Monitor vibration for 7 days, target < 40 Hz", styles['Normal']))

    doc.build(story)
    print(f"✓ Generated: vestas_v150_repair_manual.pdf")

def create_ge_turbine_manual():
    """Generate GE 7HA Gas Turbine Manual"""
    filename = os.path.join(OUTPUT_DIR, "ge_7ha_gas_turbine_manual.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.extend(create_manual_header(
        "GE 7HA.02 Gas Turbine",
        "Compressor Blade Inspection & Maintenance Manual",
        "7HA.02 - 60Hz Configuration"
    ))

    story.append(Paragraph("<b>1. COMPRESSOR BLADE INSPECTION PROCEDURE</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>1.1 Inspection Criteria</b>", styles['Heading3']))
    story.append(Paragraph("Perform blade inspection if:", styles['Normal']))
    story.append(Paragraph("• Temperature exceeds 480°C for >2 hours", styles['Normal']))
    story.append(Paragraph("• Vibration exceeds 70 Hz", styles['Normal']))
    story.append(Paragraph("• Efficiency drop >2% from baseline", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>1.2 Required Tools & PPE</b>", styles['Heading3']))
    story.append(Paragraph("• Borescope inspection camera (min 3.5mm diameter)", styles['Normal']))
    story.append(Paragraph("• Blade depth gauge (0.1mm precision)", styles['Normal']))
    story.append(Paragraph("• Heat-resistant gloves (rated 600°C)", styles['Normal']))
    story.append(Paragraph("• Respirator with P3 filters (blade coating particulates)", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>1.3 Inspection Steps</b>", styles['Heading3']))
    steps = [
        "Cool down turbine to <50°C (minimum 12 hours)",
        "Open compressor casing inspection ports (stages 1-17)",
        "Insert borescope through port 1 and inspect first-stage blades",
        "Check for: cracks, erosion, coating loss, tip rubs, FOD damage",
        "Measure blade thickness at 3 points: root, mid-span, tip",
        "Record findings in inspection log with photographic evidence",
        "If blade wear >0.5mm: schedule replacement within 500 operating hours",
        "If cracks detected: immediate shutdown and blade replacement required",
        "Clean inspection ports and reseal with high-temp gaskets",
        "Update maintenance records in Lakebase system"
    ]

    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {step}", styles['Normal']))
        story.append(Spacer(1, 0.2*cm))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>Inspection Frequency:</b> Every 4,000 operating hours or annually", styles['Normal']))
    story.append(Paragraph("<b>Critical Alert:</b> Immediate shutdown if blade detachment suspected", styles['Normal']))

    doc.build(story)
    print(f"✓ Generated: ge_7ha_gas_turbine_manual.pdf")

def create_abb_substation_manual():
    """Generate ABB Substation Manual"""
    filename = os.path.join(OUTPUT_DIR, "abb_substation_manual.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.extend(create_manual_header(
        "ABB 132kV GIS Substation",
        "Switchgear Maintenance & Arc Flash Safety Manual",
        "ZS1 Gas-Insulated Switchgear"
    ))

    story.append(Paragraph("<b>1. ARC FLASH SAFETY CHECKLIST</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("⚡ <b>DANGER - ARC FLASH HAZARD</b>", styles['Heading3']))
    story.append(Paragraph("Arc Flash Boundary: 1.2 meters", styles['Normal']))
    story.append(Paragraph("Incident Energy: 12 cal/cm² at working distance", styles['Normal']))
    story.append(Paragraph("Arc Flash Category: 3", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>1.1 Mandatory PPE (NFPA 70E Category 3)</b>", styles['Heading3']))
    ppe_data = [
        ['PPE Item', 'Specification', 'Mandatory'],
        ['Arc-rated suit', '40 cal/cm² minimum', 'YES'],
        ['Arc-rated hood', 'Face shield + balaclava', 'YES'],
        ['Insulated gloves', 'Class 3 (26.5kV rated)', 'YES'],
        ['Leather protectors', 'Over rubber gloves', 'YES'],
        ['Arc-rated boots', 'Dielectric, non-conductive', 'YES'],
        ['Voltage detector', '132kV rated', 'YES']
    ]

    ppe_table = Table(ppe_data, colWidths=[5*cm, 7*cm, 3*cm])
    ppe_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF3621')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
    ]))
    story.append(ppe_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>2. SWITCHGEAR MAINTENANCE PROCEDURE</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>2.1 Pre-Maintenance Safety Steps</b>", styles['Heading3']))
    steps = [
        "Obtain electrical permit (MCE-ELEC-132)",
        "Notify grid operator of planned outage (minimum 48h notice)",
        "De-energize 132kV busbar - confirm with two independent voltage indicators",
        "Apply grounding clamps at three points (visible grounds required)",
        "Install safety barriers at 1.5m arc flash boundary",
        "Conduct pre-job safety briefing with all personnel",
        "Verify SF6 gas pressure: 6.0 bar (at 20°C) - do not proceed if <5.5 bar"
    ]

    for step in steps:
        story.append(Paragraph(f"• {step}", styles['Normal']))
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>2.2 SF6 Gas Leak Detection</b>", styles['Heading3']))
    story.append(Paragraph("• Use calibrated SF6 leak detector (sensitivity: 1 ppm)", styles['Normal']))
    story.append(Paragraph("• Check all sealed joints and bushings", styles['Normal']))
    story.append(Paragraph("• If leak detected: evacuate area, ventilate, call hazmat team", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>Emergency Contact:</b> Arc Flash Injury - Call 000 immediately", styles['Normal']))
    story.append(Paragraph("<b>Defibrillator Location:</b> Control room - wall-mounted AED", styles['Normal']))

    doc.build(story)
    print(f"✓ Generated: abb_substation_manual.pdf")

def main():
    print("Generating mock PDF technical manuals...")
    print("=" * 60)

    create_vestas_manual()
    create_ge_turbine_manual()
    create_abb_substation_manual()

    print("\n" + "=" * 60)
    print("✅ PDF manuals generated successfully!")
    print(f"\nFiles created in: {OUTPUT_DIR}")
    print("  - vestas_v150_repair_manual.pdf")
    print("  - ge_7ha_gas_turbine_manual.pdf")
    print("  - abb_substation_manual.pdf")

if __name__ == "__main__":
    main()
