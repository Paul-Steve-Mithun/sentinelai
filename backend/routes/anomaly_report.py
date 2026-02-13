"""
Anomaly report generation routes
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import models

router = APIRouter()


def get_risk_color(risk_level: str):
    """Get color for risk level"""
    risk_colors = {
        'low': colors.green,
        'medium': colors.orange,
        'high': colors.orangered,
        'critical': colors.red
    }
    return risk_colors.get(risk_level.lower(), colors.grey)


@router.get("/{employee_id}/anomalies/report")
async def generate_anomaly_report(employee_id: str):
    """Generate PDF report of all anomalies for an employee"""
    
    # Get employee
    if PydanticObjectId.is_valid(employee_id):
        employee = await models.Employee.get(employee_id)
    else:
        employee = await models.Employee.find_one(models.Employee.employee_id == employee_id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get all anomalies for this employee
    anomalies = await models.Anomaly.find(
        models.Anomaly.employee_id == employee.id
    ).sort(-models.Anomaly.detected_at).to_list()
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    
    # Title
    elements.append(Paragraph("SentinelAI - Anomaly Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Employee Information Section
    elements.append(Paragraph("Employee Information", heading_style))
    
    employee_data = [
        ['Employee ID:', employee.employee_id],
        ['Name:', employee.name],
        ['Email:', employee.email],
        ['Department:', employee.department],
        ['Role:', employee.role],
        ['Location:', employee.baseline_location or 'N/A'],
        ['Report Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')]
    ]
    
    employee_table = Table(employee_data, colWidths=[2*inch, 4*inch])
    employee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(employee_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary Statistics
    elements.append(Paragraph("Anomaly Summary", heading_style))
    
    # Calculate statistics
    total_anomalies = len(anomalies)
    risk_breakdown = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    for anomaly in anomalies:
        risk_level = anomaly.risk_level.lower()
        if risk_level in risk_breakdown:
            risk_breakdown[risk_level] += 1
    
    summary_data = [
        ['Total Anomalies:', str(total_anomalies)],
        ['Critical Risk:', str(risk_breakdown['critical'])],
        ['High Risk:', str(risk_breakdown['high'])],
        ['Medium Risk:', str(risk_breakdown['medium'])],
        ['Low Risk:', str(risk_breakdown['low'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Anomaly Details Section
    elements.append(Paragraph("Anomaly Details", heading_style))
    
    if total_anomalies == 0:
        elements.append(Paragraph("No anomalies detected for this employee.", normal_style))
    else:
        # Create table header
        anomaly_table_data = [
            ['Detected At', 'Risk Level', 'Score', 'Type', 'Description']
        ]
        
        # Add anomaly rows
        for anomaly in anomalies:
            detected_at = anomaly.detected_at.strftime('%Y-%m-%d %H:%M')
            risk_level = anomaly.risk_level.upper()
            risk_score = str(anomaly.risk_score)
            anomaly_type = anomaly.anomaly_type.replace('_', ' ').title()
            description = anomaly.description[:80] + '...' if len(anomaly.description) > 80 else anomaly.description
            
            anomaly_table_data.append([
                detected_at,
                risk_level,
                risk_score,
                anomaly_type,
                description
            ])
        
        # Create table with appropriate column widths
        anomaly_table = Table(
            anomaly_table_data,
            colWidths=[1.3*inch, 0.9*inch, 0.6*inch, 1.2*inch, 2.5*inch]
        )
        
        # Base table style
        table_style = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Detected At
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Risk Level
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Score
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Type
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),    # Description
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]
        
        # Add color coding for risk levels
        for i, anomaly in enumerate(anomalies, start=1):
            risk_color = get_risk_color(anomaly.risk_level)
            table_style.append(('TEXTCOLOR', (1, i), (1, i), risk_color))
            table_style.append(('FONTNAME', (1, i), (1, i), 'Helvetica-Bold'))
            
            # Alternate row colors for better readability
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb')))
        
        anomaly_table.setStyle(TableStyle(table_style))
        elements.append(anomaly_table)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        "This report was automatically generated by SentinelAI - Insider Threat Detection System",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    buffer.seek(0)
    
    # Generate filename
    filename = f"SentinelAI_Anomaly_Report_{employee.employee_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Return PDF as streaming response
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
