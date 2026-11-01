import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_callout(doc, text, title="KEY PRINCIPLE", border_color="0071E3", fill_color="F0F7FF"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(6.5)
    cell = tbl.cell(0, 0)
    set_cell_background(cell, fill_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    # Left border only
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="none"/>
            <w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"[{title}] ")
    run_t.bold = True
    run_t.font.size = Pt(10)
    run_t.font.color.rgb = RGBColor(0, 80, 180)
    
    run_b = p.add_run(text)
    run_b.font.size = Pt(10)
    run_b.font.color.rgb = RGBColor(40, 40, 40)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_document(file_path):
    doc = Document()
    
    # Page setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles setup
    style_normal = doc.styles['Normal']
    font_normal = style_normal.font
    font_normal.name = 'Calibri'
    font_normal.size = Pt(11)
    font_normal.color.rgb = RGBColor(51, 51, 51)
    
    # -------------------------------------------------------------
    # Title Section
    # -------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("ReLoop AI — The Next-Life Engine for Electronics")
    run_title.bold = True
    run_title.font.size = Pt(24)
    run_title.font.color.rgb = RGBColor(16, 44, 87)
    
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(14)
    run_sub = sub_p.add_run("Prototype Architecture, Calculation Methodology & Deterministic Scoring Engine")
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(18)
    run_meta = meta_p.add_run(
        "Project: PCCoE International Grand Challenge 2026 | Category: Smart Cities, Energy & Circular Economy\n"
        "Focus: Circular Lifecycle Decision Optimization, E-Waste Reduction & Carbon Abatement"
    )
    run_meta.font.size = Pt(9.5)
    run_meta.font.italic = True
    run_meta.font.color.rgb = RGBColor(120, 120, 120)
    
    # Divider line
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(14)
    p_div_border = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="18" w:space="1" w:color="0071E3"/></w:pBdr>')
    p_div._p.get_or_add_pPr().append(p_div_border)
    
    # -------------------------------------------------------------
    # 1. Executive Summary
    # -------------------------------------------------------------
    h1 = doc.add_heading("1. Executive Summary & Purpose", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)
    
    doc.add_paragraph(
        "Modern consumer and enterprise IT hardware (specifically laptops) is overwhelmingly discarded, "
        "recycled prematurely, or stockpiled when only a single modular component degrades (e.g., degraded battery capacity, "
        "thermal paste dry-out, or sticky keyboard keys). ReLoop AI is a deterministic decision optimization engine designed "
        "to determine the highest-value, lowest-impact 'Next Life' for electronic devices before recycling is ever considered."
    )
    
    add_callout(
        doc,
        "ReLoop AI enforces the strict Circular Economy Waste Hierarchy: "
        "Repair → Upgrade → Refurbish → Reuse/Redeploy → Component Recovery → Recycling (only as a last resort). "
        "Recycling is strictly treated as a residual safeguard, never as the default action.",
        title="CIRCULAR HIERARCHY"
    )
    
    # -------------------------------------------------------------
    # 2. What Does ReLoop AI Calculate?
    # -------------------------------------------------------------
    h1 = doc.add_heading("2. What ReLoop AI Calculates (Core Metrics)", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    doc.add_paragraph(
        "For any evaluated device, ReLoop AI processes physical inspections, hardware telemetry, and diagnostic evidence to calculate "
        "the following quantitative and qualitative parameters across 6 circular pathways:"
    )
    
    metrics = [
        ("Component Health & Condition Synthesis", "Calculates operational status (GOOD, FAIR, SERVICE_REQUIRED, REPLACE_REQUIRED, UNKNOWN) for 8 modular hardware subsystems: Battery, Storage (SSD/NVMe), Memory (RAM), Thermals, Display, Keyboard, Chassis/Hinges, and System Board."),
        ("Pathway Feasibility & Eligibility", "Evaluates boolean eligibility for each circular tier against physical architecture, electrical integrity, modularity constraints (e.g. soldered vs. modular RAM), and economic viability caps."),
        ("Useful Life Extension (Years)", "Computes the projected additional lifespan in years (min, max, average) gained by executing specific corrective or restorative interventions (typically +1.5 to +4.5 years)."),
        ("Value Retained (%)", "Measures the residual economic asset value retained after intervention relative to the device's functional baseline (typically 60% to 95%)."),
        ("Material Retained (%)", "Quantifies the physical mass percentage of the original device preserved and diverted from shredding or landfills (typically 80% to 98%)."),
        ("Embodied Carbon Abatement (kg CO2e Avoided)", "Calculates the net greenhouse gas emissions avoided by extending the device life and deferring new hardware manufacturing, accounting for replacement parts emissions."),
        ("E-Waste Diverted (kg)", "Calculates the exact weight of physical electronic waste kept out of the waste stream based on the hardware catalog specifications."),
        ("Financial Restoration Cost (INR / USD)", "Aggregates localized parts acquisition and labor costs for all required component replacements, repasting, and servicing."),
        ("Logistics & Recovery Turnaround Time (Days)", "Projects the operational turnaround time in days required for sourcing parts, technician labor, testing, and redeployment."),
        ("Multi-Objective Circular Score (0–100)", "A deterministic composite score reflecting the holistic circular value under a user's chosen strategic objective (e.g., Maximum Life, Lowest Cost, Environmental Benefit, Fastest Recovery)."),
        ("Second-Life Workload Matching", "Heuristic mapping of hardware compute capacity (CPU, RAM, GPU) to productive roles (Digital Education, Linux Terminal, Remote Workstation) and recommended OS (Ubuntu 24.04 LTS, ChromeOS Flex)."),
        ("Component Salvage Manifest", "For damaged or decommissioned units, catalogs intact modular subcomponents (NVMe SSD, SO-DIMM RAM, Display panel) with market salvage valuations.")
    ]
    
    for title, desc in metrics:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        r_b = p.add_run(f"{title}: ")
        r_b.bold = True
        p.add_run(desc)
        
    # -------------------------------------------------------------
    # 3. How Does ReLoop AI Calculate It? (Architecture & Methodology)
    # -------------------------------------------------------------
    h1 = doc.add_heading("3. How ReLoop AI Calculates: The 5-Stage Pipeline", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    doc.add_paragraph(
        "ReLoop AI follows a rigorous 5-stage sequential decision pipeline designed with strict architectural separation between "
        "AI perceptual interpretation and deterministic mathematical optimization."
    )
    
    # Stage 1
    h2 = doc.add_heading("Stage 1: Input Ingestion & Evidence Provenance Layer", level=2)
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(
        "The system accepts multimodal evidence from three primary sources and assigns strict evidence provenance tiers:"
    )
    
    sources = [
        ("DIAGNOSTIC (Highest Confidence)", "Direct OS telemetry extracted from Windows Battery Reports, Linux upower/smartctl, or BIOS logs (e.g., design capacity = 54,000 mWh, full charge capacity = 38,200 mWh, cycle count = 482, SSD wear = 12%, CPU load temp = 88°C)."),
        ("VISUAL (Medium Confidence for Exterior)", "Uploaded photos analyzed by Vision AI to identify exterior physical defects: display glass cracks, casing dents, missing keycaps, hinge misalignment, port debris/bent pins, and casing swelling."),
        ("USER_REPORTED (Supplementary Confidence)", "User symptom reports (e.g., 'heats up quickly', 'battery drains in 1 hour', 'key stuck'). Note: Under ReLoop AI rules, user reports alone can NEVER declare a component GOOD."),
        ("DATABASE_SPEC", "Curated hardware catalog specifications (e.g., RAM modularity, NVMe slots, TDP, OEM part costs)."),
        ("MODEL_ESTIMATE", "Lifecycle emission benchmarks and standardized labor time standards.")
    ]
    for s_title, s_desc in sources:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"{s_title}: ")
        r.bold = True
        p.add_run(s_desc)
        
    add_callout(
        doc,
        "Crucial Guardrail: A photograph can NEVER prove internal component health. "
        "The Vision AI is explicitly prohibited from declaring battery capacity, SSD health, RAM status, or motherboard electrical health. "
        "Any visual claim regarding internal health is automatically purged by backend post-filters.",
        title="EVIDENCE INTEGRITY GUARDRAIL",
        border_color="E11D48",
        fill_color="FFF1F2"
    )
    
    # Stage 2
    h2 = doc.add_heading("Stage 2: Component Condition Synthesis", level=2)
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(
        "The Assessment Service synthesizes raw evidence into a standardized Component Condition Profile using deterministic threshold logic:"
    )
    
    # Table for component rules
    tbl = doc.add_table(rows=1, cols=4)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    col_widths = [Inches(1.2), Inches(1.8), Inches(1.8), Inches(1.7)]
    headers = ["Subsystem", "Telemetry Thresholds", "Evaluated Status", "Service Implication"]
    
    hdr_cells = tbl.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].width = col_widths[i]
        p = hdr_cells[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(title)
        r.bold = True
        r.font.size = Pt(9.5)
        set_cell_background(hdr_cells[i], "102C57")
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)
        
    table_data = [
        ("Battery", "Health ≥ 80% and Cycles < 500\nHealth 50–79% or Cycles 500–1000\nHealth < 50% or Swelling", "GOOD\nSERVICE_REQUIRED\nREPLACE_REQUIRED", "No action\nOptional reconditioning\nOEM Battery Replacement"),
        ("Thermals", "Idle < 55°C, Load < 82°C\nLoad 83–92°C or fan noise\nLoad > 92°C or thermal throttling", "GOOD\nFAIR\nSERVICE_REQUIRED", "No action\nCleaning recommendation\nHeatsink repaste & fan service"),
        ("Storage (SSD)", "SMART health ≥ 90%, 0 reallocated\nSMART 70–89%\nSMART < 70% or bad sectors", "GOOD\nFAIR\nREPLACE_REQUIRED", "Healthy\nBackup advised\nM.2 NVMe Replacement"),
        ("Display", "No cracks, no dead pixels, backlight even\nHairline bezel scratch\nGlass crack, broken LCD lines", "GOOD\nFAIR\nREPLACE_REQUIRED", "Healthy\nCosmetic acceptance\nPanel assembly swap"),
        ("Keyboard", "All keys register, clean scissor switches\nCosmetic keycap shine\nMissing keycaps, broken scissor switch", "GOOD\nFAIR\nSERVICE_REQUIRED", "Healthy\nCosmetic\nModule/keycap replacement"),
        ("System Board", "All power rails operational, POST passes\nIntermittent USB-C port connection\nShort circuit, liquid corrosion, no POST", "GOOD\nSERVICE_REQUIRED\nREPLACE_REQUIRED", "Fully functional\nPort microsoldering\nMotherboard replacement unviable")
    ]
    
    for row_idx, data in enumerate(table_data):
        row = tbl.add_row()
        fill = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            set_cell_background(cell, fill)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(text)
            r.font.size = Pt(8.5)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    # Stage 3
    h2 = doc.add_heading("Stage 3: Pathway Eligibility Evaluation (Hard Constraints)", level=2)
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(
        "Before any pathway is scored, the Rules Engine evaluates strict boolean viability criteria:"
    )
    
    eligibility_rules = [
        ("Repair Eligibility", "Motherboard must be electrically intact. Failure must be isolated to modular, serviceable components (battery, keyboard, thermal paste, display). Replacement cost must not exceed 40% of the device's replacement market value."),
        ("Upgrade Eligibility", "Base system logic board must be operational. Hardware must possess modular expansion slots (specs.ram_modular or specs.ssd_modular). Soldered architectures (e.g. Apple M-series) automatically fail upgrade eligibility."),
        ("Refurbishment Eligibility", "Device must pass core system functional checks, with restorative needs limited to cosmetic re-casing, thermal paste re-application, deep sanitation, and battery replacement."),
        ("Reuse / Redeploy Eligibility", "All core components must be in GOOD or FAIR condition. No critical repairs needed. Ideal for immediate cascading deployment to students, schools, or NGOs."),
        ("Component Recovery Eligibility", "Triggered when the core device has an irreparable motherboard or catastrophic display damage, but secondary modular subcomponents (NVMe SSD, SO-DIMM RAM, Wi-Fi card) test 100% operational and retain salvage market value."),
        ("Recycle Eligibility", "Always technically eligible as a physical baseline, but heavily penalized unless all five higher-value circular tiers are declared unviable.")
    ]
    for r_title, r_desc in eligibility_rules:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"{r_title}: ")
        r.bold = True
        p.add_run(r_desc)

    # Stage 4
    h2 = doc.add_heading("Stage 4: Mathematical Scoring & Normalization Engine", level=2)
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(
        "To compare diverse physical and economic units (years, percentages, kg CO2e, dollars, days), "
        "ReLoop AI normalizes all sub-metrics to a standard [0.0, 1.0] scale using bounded linear transformations:"
    )
    
    formulas = [
        ("Life Extension Normalization (0 to 5 Years)", "Norm_Life = min(1.0, max(0.0, Avg_Life_Years / 5.0))"),
        ("Value Retained Normalization (0 to 100%)", "Norm_Value = min(1.0, max(0.0, Value_Retained_Percentage / 100.0))"),
        ("Material Retained Normalization (0 to 100%)", "Norm_Material = min(1.0, max(0.0, Material_Retained_Percentage / 100.0))"),
        ("Environmental CO2e Avoided (0 to 300 kg)", "Norm_Env = min(1.0, max(0.0, Avg_CO2_Avoided_kg / 300.0))"),
        ("Cost Economy (0 to $300 Penalty)", "Norm_Cost = min(1.0, max(0.0, Avg_Cost_USD / 300.0))  →  Cost_Economy = 1.0 - Norm_Cost"),
        ("Logistics Speed (0 to 10 Days Penalty)", "Norm_Logistics = min(1.0, max(0.0, Avg_Turnaround_Days / 10.0))  →  Logistics_Speed = 1.0 - Norm_Logistics")
    ]
    for f_title, f_formula in formulas:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"{f_title}: ")
        r.bold = True
        r_f = p.add_run(f_formula)
        r_f.font.name = 'Consolas'
        r_f.font.size = Pt(9.5)
        
    doc.add_paragraph(
        "The final deterministic Circular Score is computed by taking the weighted sum across the normalized subscores, scaled to 100:"
    )
    
    p_box = doc.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_box = p_box.add_run(
        "Score = 100 × [ w_life · Norm_Life + w_val · Norm_Value + w_mat · Norm_Material "
        "+ w_env · Norm_Env + w_cost · (1 - Norm_Cost) + w_log · (1 - Norm_Logistics) ]"
    )
    r_box.bold = True
    r_box.font.name = 'Consolas'
    r_box.font.size = Pt(10)
    r_box.font.color.rgb = RGBColor(16, 44, 87)
    
    doc.add_paragraph(
        "ReLoop AI dynamically adjusts the weights based on the user's selected Strategic Optimization Objective:"
    )
    
    # Objective weights table
    tbl_w = doc.add_table(rows=1, cols=7)
    tbl_w.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_w.autofit = False
    
    w_widths = [Inches(1.7), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)]
    w_headers = ["Strategic Objective", "w_life", "w_val", "w_mat", "w_env", "w_cost", "w_log"]
    
    for i, t in enumerate(w_headers):
        cell = tbl_w.rows[0].cells[i]
        cell.width = w_widths[i]
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(t)
        r.bold = True
        r.font.size = Pt(9)
        set_cell_background(cell, "0F172A")
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(cell, top=100, bottom=100, left=80, right=80)
        
    w_data = [
        ("MAXIMUM_LIFE (Default)", "0.35", "0.20", "0.15", "0.15", "0.10", "0.05"),
        ("LOWEST_COST", "0.20", "0.15", "0.08", "0.07", "0.40", "0.10"),
        ("ENVIRONMENTAL_BENEFIT", "0.20", "0.10", "0.25", "0.35", "0.05", "0.05"),
        ("FASTEST_RECOVERY", "0.15", "0.25", "0.05", "0.05", "0.15", "0.35")
    ]
    for row_idx, r_vals in enumerate(w_data):
        row = tbl_w.add_row()
        fill = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(r_vals):
            c = row.cells[col_idx]
            c.width = w_widths[col_idx]
            set_cell_background(c, fill)
            set_cell_margins(c, top=80, bottom=80, left=80, right=80)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if col_idx == 0:
                r.bold = True
                
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    
    add_callout(
        doc,
        "Ineligibility & Tie-Breaking Rules:\n"
        "1. Ineligibility Penalty: If a pathway fails its eligibility constraints, its final score is penalized by an 85% reduction factor (Score = Score × 0.15) ensuring eligible options always rank higher.\n"
        "2. Deterministic Tie-Breaking: If two pathways achieve identical scores, ties are broken strictly by circular hierarchy priority: REUSE (6) > REPAIR (5) > UPGRADE (4) > REFURBISH (3) > COMPONENT RECOVERY (2) > RECYCLE (1).",
        title="DETERMINISTIC RANKING INTEGRITY"
    )

    # Stage 5
    h2 = doc.add_heading("Stage 5: Multimodal Explanation & Audit Reporting", level=2)
    h2.paragraph_format.space_before = Pt(10)
    h2.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(
        "In the final stage, ReLoop AI links every quantitative outcome back to verified evidence items (via unique evidence IDs). "
        "The system generates a full compliance audit trail, downloadable PDF/JSON reports, and plain-language technical justifications "
        "grounded strictly in observed facts—preventing AI hallucination and ensuring defensibility for enterprise asset managers."
    )
    
    # -------------------------------------------------------------
    # 4. Environmental & Carbon Abatement Mathematics
    # -------------------------------------------------------------
    h1 = doc.add_heading("4. Environmental & Carbon Abatement Methodology", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    doc.add_paragraph(
        "Manufacturing a modern business laptop generates between 250 kg and 350 kg of embodied CO2e (carbon dioxide equivalent), "
        "with over 75% to 85% of emissions occurring during silicon wafer manufacturing, PCB assembly, and chassis smelting before "
        "the laptop is ever powered on."
    )
    
    doc.add_paragraph(
        "ReLoop AI quantifies carbon abatement using the deferred-manufacturing displacement model:"
    )
    
    p_carb = doc.add_paragraph()
    p_carb.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_carb = p_carb.add_run(
        "CO2e_Avoided = [ Embodied_Emissions_New × ( Life_Extension_Years / Standard_Baseline_Life ) ] - Manufacturing_Emissions_Spare_Parts"
    )
    r_carb.bold = True
    r_carb.font.name = 'Consolas'
    r_carb.font.size = Pt(9.5)
    r_carb.font.color.rgb = RGBColor(16, 44, 87)
    
    doc.add_paragraph(
        "For example, extending the life of a Dell Latitude 5420 by 3.5 years via a battery replacement (embodied spare battery: ~8.5 kg CO2e) "
        "avoids approximately 210 kg to 275 kg of net CO2e that would have been emitted to manufacture a replacement laptop."
    )
    
    # -------------------------------------------------------------
    # 5. Validation Against 4 Canonical Demo Scenarios
    # -------------------------------------------------------------
    h1 = doc.add_heading("5. Demonstration & Validation Benchmark Cases", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    doc.add_paragraph(
        "ReLoop AI includes four canonical test cases that prove the engine selects the appropriate circular pathway across all device conditions:"
    )
    
    # Validation Table
    tbl_v = doc.add_table(rows=1, cols=5)
    tbl_v.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_v.autofit = False
    
    v_widths = [Inches(1.3), Inches(1.5), Inches(1.7), Inches(1.0), Inches(1.0)]
    v_headers = ["Demo Case", "Device Model", "Hardware Condition Summary", "Selected Loop", "Opt. Score"]
    
    for i, t in enumerate(v_headers):
        c = tbl_v.rows[0].cells[i]
        c.width = v_widths[i]
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(t)
        r.bold = True
        r.font.size = Pt(9)
        set_cell_background(c, "1E3A8A")
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_margins(c, top=100, bottom=100, left=80, right=80)
        
    v_data = [
        ("Demo 01: Healthy", "Lenovo ThinkPad T14 Gen 1", "Battery 92%, Cycles 140, SSD 98%, Thermals Normal, Pristine Exterior", "REUSE", "81.7 / 100"),
        ("Demo 02: Repairable", "Dell Latitude 5420", "Battery 54% (680 cycles), Thermals 88°C, Scratched Bottom Cover", "REPAIR", "80.4 / 100"),
        ("Demo 03: Borderline", "HP EliteBook 840 G7", "Hairline display scratch, Thermal throttling (94°C), Battery 68%", "REPAIR", "82.9 / 100"),
        ("Demo 04: Recovery", "Dell Latitude 5420", "Motherboard shorted/no POST, Crushed LCD, Functional SSD & RAM", "COMPONENT RECOVERY", "60.2 / 100")
    ]
    for row_idx, r_vals in enumerate(v_data):
        row = tbl_v.add_row()
        fill = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, val in enumerate(r_vals):
            c = row.cells[col_idx]
            c.width = v_widths[col_idx]
            set_cell_background(c, fill)
            set_cell_margins(c, top=80, bottom=80, left=80, right=80)
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if col_idx in [0, 3]:
                r.bold = True
                
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    # -------------------------------------------------------------
    # 6. Conclusion
    # -------------------------------------------------------------
    h1 = doc.add_heading("6. Conclusion & Key Takeaways", level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    
    doc.add_paragraph(
        "ReLoop AI bridges the critical gap between raw, unstructured device telemetry and high-confidence circular business decisions. "
        "By enforcing strict evidence provenance, eliminating AI hallucinations from financial and physical decision-making, and executing "
        "mathematically reproducible multi-objective optimization, the platform empowers smart cities, enterprises, and refurbishers to "
        "maximize the economic life of electronics while maximizing carbon abatement and diverting metric tons of toxic e-waste."
    )
    
    doc.save(file_path)
    print(f"Document successfully created at: {file_path}")

if __name__ == "__main__":
    target_path = r"c:\Users\DELL\OneDrive\Reloop AI\ReLoop_AI_Prototype_Summary.docx"
    build_document(target_path)
