import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "ReLoop AI — Manual Operation & Execution Guide")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)
            
        # Footer
        text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, text)
        self.drawString(54, 36, "Confidential — For Internal & Developer Use Only")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * inch - 54, 48)
        self.restoreState()

def create_code_block(code_text, styles):
    p = Paragraph(f"<font face='Courier' size='8.5'>{code_text.replace(chr(10), '<br/>')}</font>", styles['CodeStyle'])
    t = Table([[p]], colWidths=[7.2 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('LINEBEFORE', (0,0), (0,-1), 3, colors.HexColor("#0284C7")),
    ]))
    return t

def create_callout(text, box_type, styles):
    palette = {
        'info': {'bg': '#F0FDF4', 'border': '#16A34A', 'title': '[NOTE] '},
        'tip': {'bg': '#EFF6FF', 'border': '#2563EB', 'title': '[PRO TIP] '},
        'warning': {'bg': '#FFFBEB', 'border': '#D97706', 'title': '[WARNING] '}
    }
    cfg = palette.get(box_type, palette['info'])
    content = f"<b>{cfg['title']}</b> {text}"
    p = Paragraph(content, styles['CalloutStyle'])
    t = Table([[p]], colWidths=[7.2 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(cfg['bg'])),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('LINEBEFORE', (0,0), (0,-1), 3.5, colors.HexColor(cfg['border'])),
    ]))
    return t

def build_pdf():
    pdf_path = r"c:\Users\pushp\OneDrive\Desktop\AntiGravity\ReLoop_AI_Manual_Run_Guide.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0F5132"),
        spaceAfter=4,
        alignment=0
    ))
    
    styles.add(ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14
    ))
    
    styles.add(ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F5132"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A")
    ))

    styles.add(ParagraphStyle(
        'CalloutStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#1E293B")
    ))

    story = []
    
    # Title & Subtitle
    story.append(Paragraph("ReLoop AI — Manual Run & Operation Manual", styles['DocTitle']))
    story.append(Paragraph("Step-by-step instructions to configure, run, and verify the frontend and backend locally.", styles['DocSubtitle']))
    
    # Meta badge bar
    meta_data = [["PROJECT: ReLoop AI", "VERSION: 0.1.0", "OS: Windows / Cross-Platform", "STACK: Next.js 16 + FastAPI"]]
    meta_table = Table(meta_data, colWidths=[1.8 * inch] * 4)
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#334155")),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))
    
    # Section 1: Overview
    story.append(Paragraph("1. Executive Overview & Architecture", styles['H1']))
    story.append(Paragraph(
        "ReLoop AI (The Next-Life Engine for Products) is an enterprise circular economy decision engine. "
        "It evaluates electronic devices to compute the optimal circular lifecycle: Reuse, Refurbish, Repair, "
        "Remanufacture, Repurpose, or Responsible Recycle. The system combines multimodal visual defect detection "
        "(Google Gemini), diagnostic log parsing, symptom matrix triangulation, and multi-objective scoring.",
        styles['BodyDark']
    ))
    
    arch_data = [
        ["Layer", "Technology Stack", "Key Responsibilities"],
        ["Frontend Client", "Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide React", "Device inspection wizard, symptom checklists, circular pathways engine display, PDF/Excel export, Dark/Light mode."],
        ["Backend Engine", "FastAPI (Python 3.11+ / 3.14), SQLAlchemy, Pydantic v2, SQLite / PostgreSQL, Google GenAI SDK", "Multimodal vision analysis, hardware diagnostic parsing, multi-criteria pathway scoring, email OTP auth, REST endpoints."]
    ]
    arch_t = Table(arch_data, colWidths=[1.3 * inch, 2.7 * inch, 3.2 * inch])
    arch_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F5132")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.white),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F8FAFC")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(arch_t)
    story.append(Spacer(1, 10))
    
    # Section 2: Prerequisites
    story.append(Paragraph("2. Workstation Prerequisites", styles['H1']))
    prereqs = [
        "<b>Python 3.11+</b> (FastAPI backend runtime). Test via: <font face='Courier'>python --version</font>",
        "<b>Node.js (v18.17+ or v20+ / v24+)</b> (Next.js frontend runtime). Test via: <font face='Courier'>node -v</font>",
        "<b>npm (v9+ or v10+ / v11+)</b> (Node package manager). Test via: <font face='Courier'>npm -v</font>",
        "<b>Git</b> (Source control and repository synchronization). Test via: <font face='Courier'>git --version</font>"
    ]
    for p_item in prereqs:
        story.append(Paragraph(f"• {p_item}", styles['BulletText']))
    story.append(Spacer(1, 10))
    
    # Section 3: Step-by-Step Backend
    story.append(Paragraph("3. Step-by-Step: Running the Backend Manually", styles['H1']))
    story.append(Paragraph("The backend provides the REST API, AI vision integration, database ORM, and optimization algorithms.", styles['BodyDark']))
    
    story.append(Paragraph("Step 1: Open Terminal in the Backend Folder", styles['H2']))
    story.append(create_code_block("cd c:\\Users\\pushp\\OneDrive\\Desktop\\AntiGravity\\backend", styles))
    
    story.append(Paragraph("Step 2: Activate Virtual Environment (Optional)", styles['H2']))
    story.append(create_code_block("python -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1", styles))
    story.append(create_callout("If PowerShell blocks script execution, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass", "warning", styles))
    
    story.append(Paragraph("Step 3: Install Backend Dependencies", styles['H2']))
    story.append(create_code_block("pip install -r requirements.txt", styles))
    
    story.append(Paragraph("Step 4: Verify Environment Configuration (.env)", styles['H2']))
    env_str = (
        "PORT=8000\n"
        "HOST=0.0.0.0\n"
        "ENVIRONMENT=development\n"
        "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n"
        "DATABASE_URL=sqlite:///./reloop.db\n"
        "DISABLE_SQLALCHEMY_CEXT=1\n"
        "GEMINI_API_KEY=<Your_Google_Gemini_API_Key>\n"
        "GEMINI_MODEL=gemini-flash-latest"
    )
    story.append(create_code_block(env_str, styles))
    
    story.append(Paragraph("Step 5: Start the FastAPI Server with Uvicorn", styles['H2']))
    story.append(create_code_block("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload", styles))
    
    story.append(Paragraph("Step 6: Test Backend Status", styles['H2']))
    story.append(Paragraph(
        "• Health Endpoint: <font face='Courier'>http://127.0.0.1:8000/health</font> (returns {\"status\": \"ok\"})<br/>"
        "• Swagger Interactive API Docs: <font face='Courier'>http://127.0.0.1:8000/docs</font><br/>"
        "• ReDoc Alternative Documentation: <font face='Courier'>http://127.0.0.1:8000/redoc</font>",
        styles['BodyDark']
    ))
    story.append(Spacer(1, 10))
    
    # Section 4: Step-by-Step Frontend
    story.append(Paragraph("4. Step-by-Step: Running the Frontend Manually", styles['H1']))
    story.append(Paragraph("Keep the backend terminal open, then launch a <b>NEW terminal window</b> for the Next.js client:", styles['BodyDark']))
    
    story.append(Paragraph("Step 1: Open Terminal in the Frontend Folder", styles['H2']))
    story.append(create_code_block("cd c:\\Users\\pushp\\OneDrive\\Desktop\\AntiGravity\\frontend", styles))
    
    story.append(Paragraph("Step 2: Install Node Dependencies", styles['H2']))
    story.append(create_code_block("npm install", styles))
    
    story.append(Paragraph("Step 3: Verify Frontend Environment (.env.local)", styles['H2']))
    f_env_str = (
        "NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000\n"
        "NEXT_PUBLIC_GEMINI_API_KEY=<Your_Google_Gemini_API_Key>\n"
        "GEMINI_MODEL=gemini-flash-latest"
    )
    story.append(create_code_block(f_env_str, styles))
    
    story.append(Paragraph("Step 4: Start the Next.js Development Server", styles['H2']))
    story.append(create_code_block("npm run dev", styles))
    
    story.append(Paragraph("Step 5: Access the Web App in Your Browser", styles['H2']))
    story.append(create_code_block("http://localhost:3000", styles))
    story.append(create_callout("Both backend and frontend terminals must remain running simultaneously in separate windows.", "tip", styles))
    story.append(Spacer(1, 10))
    
    # Section 5: Feature Verification
    story.append(Paragraph("5. Feature & Workflow Verification Checklist", styles['H1']))
    checks = [
        "<b>Landing Page (http://localhost:3000):</b> Verify hero section, circularity metrics, dynamic light effect, and interactive pathway cards.",
        "<b>Theme Toggle:</b> Click the Sun/Moon icon in the navbar to test seamless Dark/Light mode switching.",
        "<b>Device Assessment Wizard (http://localhost:3000/assess-device):</b> Upload an image, check cosmetic/hardware symptoms, and provide specs.",
        "<b>Circular Engine Results (http://localhost:3000/engine):</b> Review ranked pathways (Reuse, Refurbish, Repair, Repurpose, Recycle), salvage value, and CO2 emissions.",
        "<b>Report Export:</b> Test downloading the assessment results via the PDF and Excel export buttons.",
        "<b>Authentication:</b> Click 'Sign In' to verify Google OAuth and Email OTP login flows."
    ]
    for chk in checks:
        story.append(Paragraph(f"• {chk}", styles['BulletText']))
    story.append(Spacer(1, 10))

    # Section 6: Docker Option
    story.append(Paragraph("6. Docker Deployment (Optional)", styles['H1']))
    story.append(Paragraph("To run the full stack containerized using Docker Compose:", styles['BodyDark']))
    story.append(create_code_block("docker compose up --build\n\n# To stop:\ndocker compose down", styles))
    story.append(Spacer(1, 10))
    
    # Section 7: Troubleshooting
    story.append(Paragraph("7. Troubleshooting & Common Issues", styles['H1']))
    faq_data = [
        ["Scenario", "Resolution Steps"],
        ["Port 8000 or 3000 already in use", "Identify the process: Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess\nTerminate if needed: Stop-Process -Id <PID> -Force"],
        ["PowerShell script execution disabled", "Run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"],
        ["CORS error in browser", "Verify backend/.env has CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000"],
        ["Gemini API quota or key missing", "If GEMINI_API_KEY is not configured, ReLoop AI automatically activates rule-based heuristic fallbacks."]
    ]
    faq_t = Table(faq_data, colWidths=[2.2 * inch, 5.0 * inch])
    faq_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F5132")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('BACKGROUND', (0,1), (-1,1), colors.white),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0,3), (-1,3), colors.white),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor("#F8FAFC")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(faq_t)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
