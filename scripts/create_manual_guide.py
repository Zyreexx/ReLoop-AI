import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set the background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_code_block(doc, code_text):
    """Render a styled code snippet block with grey background."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    # Left border accent
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="0284C7"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(15, 23, 42) # Slate 900
    
    # Empty space after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(2)
    p_after.paragraph_format.space_after = Pt(4)

def add_callout(doc, text, box_type="info"):
    """Render a highlighted callout box (info, tip, warning)."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    
    bg_colors = {
        "info": "F0FDF4",      # Light Green
        "tip": "EFF6FF",       # Light Blue
        "warning": "FFFBEB"    # Light Yellow
    }
    border_colors = {
        "info": "16A34A",
        "tip": "2563EB",
        "warning": "D97706"
    }
    prefixes = {
        "info": "[NOTE] ",
        "tip": "[PRO TIP] ",
        "warning": "[WARNING] "
    }
    
    fill = bg_colors.get(box_type, "F8FAFC")
    border_col = border_colors.get(box_type, "64748B")
    
    set_cell_background(cell, fill)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="28" w:space="0" w:color="{border_col}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    
    bold_run = p.add_run(prefixes.get(box_type, ""))
    bold_run.bold = True
    bold_run.font.name = "Calibri"
    bold_run.font.size = Pt(10)
    
    text_run = p.add_run(text)
    text_run.font.name = "Calibri"
    text_run.font.size = Pt(10)
    text_run.font.color.rgb = RGBColor(30, 41, 59)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(2)
    p_after.paragraph_format.space_after = Pt(4)

def build_manual_document():
    doc = docx.Document()
    
    # Page setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)
        
    # Styles configuration
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(30, 41, 59) # Slate 800
    
    # Header / Title Banner
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("ReLoop AI — System Execution & Manual Operation Manual")
    title_run.font.name = "Calibri"
    title_run.font.size = Pt(22)
    title_run.bold = True
    title_run.font.color.rgb = RGBColor(15, 81, 50) # Deep Emerald
    
    subtitle_p = doc.add_paragraph()
    subtitle_p.paragraph_format.space_before = Pt(0)
    subtitle_p.paragraph_format.space_after = Pt(18)
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle_p.add_run("Comprehensive Technical Walkthrough and Step-by-Step Guide to Run ReLoop AI Locally")
    sub_run.font.name = "Calibri"
    sub_run.font.size = Pt(12)
    sub_run.italic = True
    sub_run.font.color.rgb = RGBColor(100, 116, 139) # Slate 500
    
    # Meta bar
    meta_tbl = doc.add_table(rows=1, cols=4)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_cols = ["Project: ReLoop AI", "Version: 0.1.0", "OS: Windows / Cross-Platform", "Stack: FastAPI + Next.js 16"]
    for i, text in enumerate(meta_cols):
        cell = meta_tbl.cell(0, i)
        set_cell_background(cell, "F8FAFC")
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text)
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(71, 85, 105)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Section 1: Executive Overview
    h1 = doc.add_heading("1. Executive Overview & System Architecture", level=1)
    h1.paragraph_format.space_before = Pt(16)
    h1.paragraph_format.space_after = Pt(6)
    for run in h1.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph()
    p.add_run(
        "ReLoop AI (The Next-Life Engine for Products) is an enterprise circular economy optimization platform. "
        "It evaluates electronic devices (laptops, phones, tablets, peripherals) to determine their optimal circular pathway: "
        "Reuse, Refurbish, Repair, Remanufacture, Repurpose, or Responsible Recycle. "
        "The system combines multimodal visual defect detection (Google Gemini), diagnostic metric parsing, symptom triangulation, "
        "and a multi-objective scoring engine."
    )
    
    # Table of Architecture
    arch_tbl = doc.add_table(rows=3, cols=3)
    arch_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Layer", "Technology Stack", "Core Responsibilities"]
    for i, h in enumerate(headers):
        cell = arch_tbl.cell(0, i)
        set_cell_background(cell, "0F5132")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(10)
        
    data = [
        ("Frontend Client", "Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide React", "Interactive inspection wizard, symptom forms, pathway dashboards, PDF/Excel export, Dark/Light theme."),
        ("Backend Engine", "FastAPI (Python 3.11+ / 3.14), SQLAlchemy, Pydantic v2, SQLite / PostgreSQL, Google GenAI SDK", "Multimodal visual inspection, diagnostic log analysis, multi-criteria pathway scoring, email OTP auth, REST endpoints.")
    ]
    for row_idx, row_data in enumerate(data, start=1):
        bg = "FFFFFF" if row_idx % 2 == 1 else "F8FAFC"
        for col_idx, text in enumerate(row_data):
            cell = arch_tbl.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Section 2: Prerequisites
    h2 = doc.add_heading("2. System Prerequisites", level=1)
    h2.paragraph_format.space_before = Pt(16)
    h2.paragraph_format.space_after = Pt(6)
    for run in h2.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph("Ensure the following tools are installed on your workstation prior to running the platform:")
    prereqs = [
        ("Python 3.11+", "Required for FastAPI backend. Verify via: python --version"),
        ("Node.js (v18.17+ or v20+ / v24+)", "Required for Next.js frontend. Verify via: node -v"),
        ("npm (v9+ or v10+ / v11+)", "Node package manager. Verify via: npm -v"),
        ("Git", "For cloning repository updates. Verify via: git --version")
    ]
    for item, desc in prereqs:
        p_item = doc.add_paragraph(style='List Bullet')
        p_item.paragraph_format.space_after = Pt(3)
        r_bold = p_item.add_run(f"{item}: ")
        r_bold.bold = True
        p_item.add_run(desc)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    
    # Section 3: Directory Layout
    h3 = doc.add_heading("3. Project Directory Map", level=1)
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(6)
    for run in h3.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph("The workspace is structured into two autonomous, loosely coupled applications:")
    dir_code = (
        "AntiGravity/\n"
        "├── backend/                 # FastAPI REST API & Optimization Engine\n"
        "│   ├── app/\n"
        "│   │   ├── main.py          # FastAPI application entrypoint\n"
        "│   │   ├── config.py        # Environment & Pydantic settings\n"
        "│   │   ├── api/routes/      # REST API endpoints (vision, products, assessment, auth, health)\n"
        "│   │   ├── models/          # SQLAlchemy ORM models (Product, Assessment, Evidence, User)\n"
        "│   │   ├── services/        # Vision, diagnostic, recommendation & report services\n"
        "│   │   ├── optimizer/       # Multi-criteria scoring, pathway algorithms & rules\n"
        "│   │   └── ai/              # Google Gemini LLM & multimodal vision clients\n"
        "│   ├── requirements.txt     # Python backend dependencies\n"
        "│   ├── .env                 # Backend runtime environment configuration\n"
        "│   └── reloop.db            # Local SQLite database file\n"
        "│\n"
        "└── frontend/                # Next.js 16 Web Application\n"
        "    ├── app/                 # Next.js App Router (pages: /, /assess-device, /engine, /pathways)\n"
        "    ├── components/          # Reusable UI components (auth, assess, engine, layout)\n"
        "    ├── context/             # ThemeContext (Dark/Light Mode)\n"
        "    ├── package.json         # Frontend npm scripts & dependencies\n"
        "    └── .env.local           # Next.js client environment variables\n"
    )
    add_code_block(doc, dir_code)
    
    # Section 4: Step-by-Step Backend
    h4 = doc.add_heading("4. Step-by-Step Instructions: Running the Backend", level=1)
    h4.paragraph_format.space_before = Pt(16)
    h4.paragraph_format.space_after = Pt(6)
    for run in h4.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph("Follow these exact steps to launch the FastAPI backend server:")
    
    # Step 4.1
    p = doc.add_paragraph()
    r = p.add_run("Step 1: Open Terminal in the Backend Folder")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Open Windows PowerShell or Command Prompt and change directory into the backend folder:")
    add_code_block(doc, "cd c:\\Users\\pushp\\OneDrive\\Desktop\\AntiGravity\\backend")
    
    # Step 4.2
    p = doc.add_paragraph()
    r = p.add_run("Step 2: Create & Activate Python Virtual Environment (Optional but Recommended)")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Isolate python dependencies inside an isolated environment:")
    add_code_block(doc, "python -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1")
    add_callout(doc, "If PowerShell gives an ExecutionPolicy script error, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass", "warning")
    
    # Step 4.3
    p = doc.add_paragraph()
    r = p.add_run("Step 3: Install Required Dependencies")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Install FastAPI, Uvicorn, SQLAlchemy, Google GenAI SDK, and Pydantic:")
    add_code_block(doc, "pip install -r requirements.txt")
    
    # Step 4.4
    p = doc.add_paragraph()
    r = p.add_run("Step 4: Verify Environment File (.env)")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Verify that backend/.env contains the proper configuration settings:")
    env_code = (
        "PORT=8000\n"
        "HOST=0.0.0.0\n"
        "ENVIRONMENT=development\n"
        "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n"
        "DATABASE_URL=sqlite:///./reloop.db\n"
        "DISABLE_SQLALCHEMY_CEXT=1\n"
        "GEMINI_API_KEY=<Your_Google_Gemini_API_Key>\n"
        "GEMINI_MODEL=gemini-flash-latest"
    )
    add_code_block(doc, env_code)
    
    # Step 4.5
    p = doc.add_paragraph()
    r = p.add_run("Step 5: Start the Uvicorn ASGI Server")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Execute the following command to start the backend with automatic hot-reloading:")
    add_code_block(doc, "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    
    # Step 4.6
    p = doc.add_paragraph()
    r = p.add_run("Step 6: Confirm Backend Health")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Open your web browser or run curl to test the endpoints:")
    add_code_block(doc, "Health check URL: http://127.0.0.1:8000/health\nInteractive Swagger Docs: http://127.0.0.1:8000/docs\nReDoc Documentation: http://127.0.0.1:8000/redoc")
    add_callout(doc, "A successful response from http://127.0.0.1:8000/health returns JSON: {\"status\": \"ok\"}", "info")
    
    # Section 5: Step-by-Step Frontend
    h5 = doc.add_heading("5. Step-by-Step Instructions: Running the Frontend", level=1)
    h5.paragraph_format.space_before = Pt(16)
    h5.paragraph_format.space_after = Pt(6)
    for run in h5.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph("Keep the backend terminal running, and open a NEW terminal window to start the Next.js frontend:")
    
    # Step 5.1
    p = doc.add_paragraph()
    r = p.add_run("Step 1: Open a Second Terminal in the Frontend Folder")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    add_code_block(doc, "cd c:\\Users\\pushp\\OneDrive\\Desktop\\AntiGravity\\frontend")
    
    # Step 5.2
    p = doc.add_paragraph()
    r = p.add_run("Step 2: Install Node Packages")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Install all frontend packages (Next.js 16, React 19, Tailwind v4, Lucide React, etc.):")
    add_code_block(doc, "npm install")
    
    # Step 5.3
    p = doc.add_paragraph()
    r = p.add_run("Step 3: Verify Frontend Environment (.env.local)")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Ensure frontend/.env.local points to the backend server:")
    f_env = (
        "NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000\n"
        "NEXT_PUBLIC_GEMINI_API_KEY=<Your_Google_Gemini_API_Key>\n"
        "GEMINI_MODEL=gemini-flash-latest"
    )
    add_code_block(doc, f_env)
    
    # Step 5.4
    p = doc.add_paragraph()
    r = p.add_run("Step 4: Launch the Next.js Development Server")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Start the dev server with hot-module reloading:")
    add_code_block(doc, "npm run dev")
    
    # Step 5.5
    p = doc.add_paragraph()
    r = p.add_run("Step 5: Access the Web Application")
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(37, 99, 235)
    doc.add_paragraph("Open your browser and navigate to:")
    add_code_block(doc, "http://localhost:3000")
    add_callout(doc, "Both servers must remain running simultaneously in separate terminal windows.", "tip")
    
    # Section 6: Workflow Verification
    h6 = doc.add_heading("6. Testing & Verifying the Application Features", level=1)
    h6.paragraph_format.space_before = Pt(16)
    h6.paragraph_format.space_after = Pt(6)
    for run in h6.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph("Once both servers are running, test the core features across the platform:")
    
    test_steps = [
        ("1. Landing Page (http://localhost:3000)", "Verify that the hero section, dynamic metrics, interactive pathway cards, and animated light effects render cleanly."),
        ("2. Theme Switching", "Click the sun/moon toggle button in the navigation header to switch seamlessly between Dark Mode and Light Mode."),
        ("3. Device Assessment Wizard (http://localhost:3000/assess-device)", "Upload or select a sample device image, check cosmetic & hardware symptoms, and provide hardware specs."),
        ("4. Decision Engine (http://localhost:3000/engine)", "Review ranked circular pathways (Reuse, Refurbish, Repair, Repurpose, Recycle), salvage estimates, and CO2 emissions avoided."),
        ("5. Exporting Reports", "Test the PDF and Excel export buttons on the engine summary page to download circular economy reports."),
        ("6. Authentication Modal", "Click the 'Sign In' button on the navbar to test Google OAuth or the email verification OTP flow.")
    ]
    for title, desc in test_steps:
        p_t = doc.add_paragraph(style='List Bullet')
        p_t.paragraph_format.space_after = Pt(4)
        r_b = p_t.add_run(f"{title}: ")
        r_b.bold = True
        p_t.add_run(desc)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    
    # Section 7: Docker Option
    h7 = doc.add_heading("7. Alternative: Running with Docker Compose", level=1)
    h7.paragraph_format.space_before = Pt(16)
    h7.paragraph_format.space_after = Pt(6)
    for run in h7.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    p = doc.add_paragraph("If Docker Desktop is installed, you can launch both backend and database with a single command:")
    add_code_block(doc, "docker compose up --build")
    doc.add_paragraph("To stop all containers gracefully:")
    add_code_block(doc, "docker compose down")
    
    # Section 8: Troubleshooting & FAQ
    h8 = doc.add_heading("8. Troubleshooting & Common Issues", level=1)
    h8.paragraph_format.space_before = Pt(16)
    h8.paragraph_format.space_after = Pt(6)
    for run in h8.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(15, 81, 50)
        
    tbl_faq = doc.add_table(rows=5, cols=2)
    tbl_faq.alignment = WD_TABLE_ALIGNMENT.CENTER
    faq_headers = ["Issue / Error Scenario", "Resolution Steps"]
    for i, h in enumerate(faq_headers):
        cell = tbl_faq.cell(0, i)
        set_cell_background(cell, "0F5132")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        r.font.size = Pt(10)
        
    faq_data = [
        ("Port 8000 or Port 3000 already in use", 
         "Check what process is holding the port:\nPowerShell: Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess\nTerminate if needed: Stop-Process -Id <PID> -Force"),
        ("PowerShell script execution disabled (.ps1 cannot be loaded)",
         "Run PowerShell as Administrator or bypass for current process:\nSet-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"),
        ("CORS error in browser console",
         "Verify backend/.env has CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\nEnsure you access http://localhost:3000 or http://127.0.0.1:3000 matching the CORS list."),
        ("Google Gemini API error or quota limit",
         "Verify valid GEMINI_API_KEY in backend/.env. If key is unset or unavailable, ReLoop AI's rule-based fallback heuristics will automatically take over.")
    ]
    for row_idx, (q, a) in enumerate(faq_data, start=1):
        bg = "FFFFFF" if row_idx % 2 == 1 else "F8FAFC"
        cell_q = tbl_faq.cell(row_idx, 0)
        cell_a = tbl_faq.cell(row_idx, 1)
        set_cell_background(cell_q, bg)
        set_cell_background(cell_a, bg)
        set_cell_margins(cell_q, top=80, bottom=80, left=100, right=100)
        set_cell_margins(cell_a, top=80, bottom=80, left=100, right=100)
        
        pq = cell_q.paragraphs[0]
        rq = pq.add_run(q)
        rq.font.bold = True
        rq.font.size = Pt(9.5)
        
        pa = cell_a.paragraphs[0]
        ra = pa.add_run(a)
        ra.font.size = Pt(9.5)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(16)
    
    # Save document
    output_filename = "ReLoop_AI_Manual_Run_Guide.docx"
    output_path = os.path.join(r"c:\Users\pushp\OneDrive\Desktop\AntiGravity", output_filename)
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    build_manual_document()
