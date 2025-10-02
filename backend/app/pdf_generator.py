# backend/app/pdf_generator.py
import io
import logging
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

from app import models

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Generate PDF documents for court judgments and orders"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Create custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY
        )
    
    def generate_judgment_pdf(self, judgment: models.Judgment, case: models.Case, query: models.Query) -> bytes:
        """Generate PDF for a judgment/order"""
        try:
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            if case.court_name:
                court_title = "IN THE " + case.court_name.upper()
            else:
                court_title = "IN THE HIGH COURT"
            
            story.append(Paragraph(court_title, self.title_style))
            story.append(Spacer(1, 20))
            
            # Case details table
            filing_date_str = case.filing_date.strftime('%d.%m.%Y') if case.filing_date else 'N/A'
            case_number_str = str(query.case_number) + "/" + str(query.year)
            
            case_data = [
                ['Case Type:', query.case_type],
                ['Case Number:', case_number_str],
                ['Filing Date:', filing_date_str],
                ['Judge:', case.judge_name or 'Hon\'ble Court'],
                ['Court Hall:', case.court_hall or 'N/A']
            ]
            
            case_table = Table(case_data, colWidths=[2*inch, 4*inch])
            case_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(case_table)
            story.append(Spacer(1, 30))
            
            # Parties
            story.append(Paragraph("PARTIES", self.header_style))
            
            petitioner_text = "<b>Petitioner:</b><br/>" + (case.parties_petitioner or 'Not Available')
            story.append(Paragraph(petitioner_text, self.body_style))
            
            respondent_text = "<b>Respondent:</b><br/>" + (case.parties_respondent or 'Not Available')
            story.append(Paragraph(respondent_text, self.body_style))
            
            story.append(Spacer(1, 20))
            
            # Order/Judgment details
            judgment_title = judgment.judgment_type.upper()
            if judgment.judgment_date:
                date_str = judgment.judgment_date.strftime('%d.%m.%Y')
                judgment_title += " DATED " + date_str
            
            story.append(Paragraph(judgment_title, self.header_style))
            story.append(Spacer(1, 15))
            
            # Sample order content
            order_content = self._generate_sample_order_content(case, judgment, query)
            story.append(Paragraph(order_content, self.body_style))
            
            story.append(Spacer(1, 30))
            
            # Footer
            current_time = datetime.now().strftime('%d.%m.%Y at %H:%M:%S')
            footer_text = """
            <b>Note:</b> This is a sample document generated for educational purposes by the 
            Indian Court Case & Cause List Tracker application. This is not a real court document.
            <br/><br/>
            Generated on: """ + current_time
            
            story.append(Paragraph(footer_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info("Generated PDF for judgment %d, size: %d bytes", judgment.id, len(pdf_bytes))
            return pdf_bytes
            
        except Exception as e:
            logger.error("Error generating PDF for judgment %d: %s", judgment.id, str(e))
            raise
    
    def _generate_sample_order_content(self, case: models.Case, judgment: models.Judgment, query: models.Query) -> str:
        """Generate realistic sample order content"""
        
        # Format dates safely
        next_hearing_str = '[Next Date]'
        if case.next_hearing_date:
            next_hearing_str = case.next_hearing_date.strftime('%d.%m.%Y')
        
        judgment_date_str = datetime.now().strftime('%d.%m.%Y')
        if judgment.judgment_date:
            judgment_date_str = judgment.judgment_date.strftime('%d.%m.%Y')
        
        if judgment.judgment_type == 'ORDER':
            content = """
            This matter came up for hearing today. The learned counsel for the petitioner was present. 
            The learned counsel for the respondent was also present.
            <br/><br/>
            Having heard the learned counsel for the parties and having perused the record, this Court is of the 
            considered opinion that the matter requires detailed consideration.
            <br/><br/>
            <b>ORDER:</b>
            <br/><br/>
            1. The matter is adjourned for hearing to """ + next_hearing_str + """.
            <br/><br/>
            2. The parties are directed to file their respective written submissions, if any, one week prior to the next date of hearing.
            <br/><br/>
            3. Office is directed to list this matter on """ + next_hearing_str + """.
            <br/><br/>
            """
        else:
            content = """
            This """ + judgment.judgment_type.lower() + """ has been reserved for consideration after hearing the learned counsel 
            for the parties.
            <br/><br/>
            The facts giving rise to this """ + query.case_type + """ are that [case facts would be detailed here in a real judgment].
            <br/><br/>
            <b>JUDGMENT:</b>
            <br/><br/>
            After careful consideration of the submissions made by the learned counsel for the parties and the material 
            on record, this Court finds that the matter requires disposal as follows:
            <br/><br/>
            1. The petition is disposed of with the following directions.
            <br/><br/>
            2. The parties shall comply with the terms as may be agreed upon.
            <br/><br/>
            """
        
        judge_name = case.judge_name or 'Hon\'ble Judge'
        content += """
        <br/>
        <br/>
        <br/>
        <div align="right">
        ( """ + judge_name + """ )<br/>
        """ + judgment_date_str + """
        </div>
        """
        
        return content

# Create global PDF generator instance
pdf_generator = PDFGenerator()
