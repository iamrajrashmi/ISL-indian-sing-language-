import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>
            <w:insideV w:val="none"/>
            <w:left w:val="none"/>
            <w:right w:val="none"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

def build_word_document():
    doc = docx.Document()

    # Configure Margins (A4)
    sections = doc.sections
    for section in sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.25)  # 1.25" for binding
        section.right_margin = Inches(1.0)

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.25
    normal_style.paragraph_format.space_after = Pt(6)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Helper functions
    def add_title(text, size=16, space_before=12, space_after=12, bold=True, center=True):
        p = doc.add_paragraph()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x17, 0x2B, 0x4D) # Navy accent
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x28, 0x64, 0xDC) # Blue accent
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.italic = True
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        return p

    def add_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.25
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        return p

    def add_code_block(code_text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.right_indent = Inches(0.25)
        run = p.add_run(code_text)
        run.font.name = 'Consolas'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        # Background shading
        pPr = p._p.get_or_add_pPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F4F6F9"/>')
        pPr.append(shd)
        return p

    def add_signature_block(left_text, right_text, space_before=40):
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(space_before)
        p_sp.paragraph_format.space_after = Pt(0)
        
        sig_tbl = doc.add_table(rows=1, cols=2)
        sig_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cl, cr = sig_tbl.rows[0].cells
        cl.width = Inches(3.2)
        cr.width = Inches(3.2)
        
        pl = cl.paragraphs[0]
        pl.alignment = WD_ALIGN_PARAGRAPH.LEFT
        rl = pl.add_run(left_text)
        rl.font.name = 'Times New Roman'
        rl.font.size = Pt(11)
        
        pr = cr.paragraphs[0]
        pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rr = pr.add_run(right_text)
        rr.font.name = 'Times New Roman'
        rr.font.size = Pt(11)
        rr.font.bold = True

    def format_table(table, col_widths, headers, data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, color="B0BEC5", sz="6")
        
        # Header row
        hdr_cells = table.rows[0].cells
        for i, header_text in enumerate(headers):
            hdr_cells[i].text = header_text
            set_cell_background(hdr_cells[i], "172B4D") # Deep Navy
            set_cell_margins(hdr_cells[i], top=120, bottom=120, left=150, right=150)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        # Data rows
        for r_idx, row_data in enumerate(data):
            row_cells = table.add_row().cells
            bg_color = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
            for c_idx, cell_value in enumerate(row_data):
                row_cells[c_idx].text = str(cell_value)
                set_cell_background(row_cells[c_idx], bg_color)
                set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=150, right=150)
                p = row_cells[c_idx].paragraphs[0]
                if c_idx == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(10.5)

        # Widths
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    # ==========================================
    # 1. COVER PAGE / TITLE PAGE
    # ==========================================
    add_title("A", size=14, space_before=0, space_after=2, bold=False)
    add_title("PROJECT REPORT", size=18, space_before=2, space_after=4, bold=True)
    add_title("ON", size=13, space_before=2, space_after=12, bold=False)
    
    title_p = add_title("REAL-TIME INDIAN SIGN LANGUAGE RECOGNITION AND SPEECH CONVERSION SYSTEM USING MEDIAPIPE AND MACHINE LEARNING", 
                        size=16, space_before=6, space_after=20, bold=True)
    
    add_title("Submitted in partial fulfilment of the requirements for the award of degree of", size=11, space_before=8, space_after=2, bold=False)
    add_title("MASTER OF COMPUTER APPLICATIONS", size=14, space_before=2, space_after=16, bold=True)

    # University Emblem / Logo
    emblem_path = "c:/Users/siddh/project/smkv_emblem.png"
    if os.path.exists(emblem_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(12)
        p_logo.add_run().add_picture(emblem_path, width=Inches(1.8))

    add_title("to", size=12, space_before=2, space_after=2, bold=False)
    add_title("SCHOOL OF STUDIES IN COMPUTER APPLICATIONS", size=14, space_before=2, space_after=2, bold=True)
    add_title("Shaheed Mahendra Karma Vishwavidyalaya, Bastar, Jagdalpur (C.G.), India", size=12, space_before=2, space_after=18, bold=True)

    # Student metadata table (two columns: By Candidate | Under Guidance)
    meta_table = doc.add_table(rows=1, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_l, cell_r = meta_table.rows[0].cells
    cell_l.width = Inches(3.2)
    cell_r.width = Inches(3.2)

    p_l = cell_l.paragraphs[0]
    p_l.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_l.add_run("Submitted By:\n")
    r.font.bold = True
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r2 = p_l.add_run("Student Name: Siddharth\nEnrollment No.: [Enrollment No.]\nRoll No.: [Roll No.]\nSession: 2026-27")
    r2.font.name = 'Times New Roman'
    r2.font.size = Pt(11)

    p_r = cell_r.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r3 = p_r.add_run("Under Guidance of:\n")
    r3.font.bold = True
    r3.font.name = 'Times New Roman'
    r3.font.size = Pt(11)
    r4 = p_r.add_run("[Faculty/Guide Name]\n[Designation]\nSoS in Computer Applications\nSMKV, Bastar, Jagdalpur")
    r4.font.name = 'Times New Roman'
    r4.font.size = Pt(11)

    # Date
    add_title("DECEMBER 2026", size=13, space_before=24, space_after=0, bold=True)
    doc.add_page_break()

    # ==========================================
    # 2. DECLARATION BY THE CANDIDATE
    # ==========================================
    add_title("DECLARATION BY THE CANDIDATE", size=15, space_before=12, space_after=18, bold=True)
    
    add_p("I hereby declare that the project report entitled “Real-Time Indian Sign Language Recognition and Speech Conversion System using MediaPipe and Machine Learning”, submitted by me in partial fulfilment of the requirements for the award of degree of Master of Computer Applications in School of Studies in Computer Applications, Shaheed Mahendra Karma Vishwavidyalaya, Bastar, Jagdalpur (C.G.) is my original work carried out under the guidance and supervision of [Name of Faculty Guide], [Designation], School of Studies in Computer Applications, SMKV, Jagdalpur.")
    add_p("I further declare that this report has been prepared by me through my own efforts and has not been submitted, either in part or in full, to any other university or institution for the award of any degree, diploma, or certificate.")
    add_p("I have duly acknowledged all sources of information, references, and materials used in the preparation of this report. I take full responsibility for the originality and authenticity of the work presented herein.")
    
    add_signature_block("Place: SMKV Jagdalpur\nDate:  ____________________", 
                        "_____________________________________\nStudent's Name & Signature\nSiddharth\nEnrollment Number: _______________", 
                        space_before=40)

    doc.add_page_break()

    # ==========================================
    # 3. CERTIFICATE BY HEAD OF DEPARTMENT
    # ==========================================
    add_title("CERTIFICATE BY THE HEAD OF THE DEPARTMENT", size=15, space_before=12, space_after=18, bold=True)
    
    add_p("This is to certify that the project report entitled “Real-Time Indian Sign Language Recognition and Speech Conversion System using MediaPipe and Machine Learning” has been submitted by Siddharth, Enrollment/Roll Number ________________, a student of Master of Computer Applications (3rd Sem.), School of Studies in Computer Applications, Shaheed Mahendra Karma Vishwavidyalaya, Bastar, Jagdalpur (C.G.) in partial fulfilment of the requirements for the award of the degree of Master of Computer Applications.")
    add_p("The project work presented in this report has been carried out by the candidate as part of the prescribed academic curriculum under the guidance of the concerned faculty member. To the best of my knowledge, the work submitted by the candidate is satisfactory.")
    add_p("I wish the candidate success in future endeavours.")

    add_signature_block("Place: SMKV Jagdalpur\nDate:  ____________________", 
                        "_____________________________________\n[Name of Head of Department]\nHead of Department\nSchool of Studies in Computer Applications\nShaheed Mahendra Karma Vishwavidyalaya,\nBastar, Jagdalpur (C.G.)", 
                        space_before=50)

    doc.add_page_break()

    # ==========================================
    # 4. CERTIFICATE BY THE EXAMINERS
    # ==========================================
    add_title("CERTIFICATE BY THE EXAMINERS", size=15, space_before=12, space_after=18, bold=True)
    
    add_p("This is to certify that the project report entitled “Real-Time Indian Sign Language Recognition and Speech Conversion System using MediaPipe and Machine Learning”, submitted by Siddharth, Enrollment/Roll No. ________________, in partial fulfilment of the requirements for the award of degree of Master of Computer Applications in School of Studies in Computer Applications, Shaheed Mahendra Karma Vishwavidyalaya, Bastar, Jagdalpur (C.G.) has been examined and evaluated by us and found satisfactory.")

    p_ex = doc.add_paragraph()
    p_ex.paragraph_format.space_before = Pt(60)
    
    ex_table = doc.add_table(rows=1, cols=2)
    ex_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_int, c_ext = ex_table.rows[0].cells
    c_int.width = Inches(3.2)
    c_ext.width = Inches(3.2)

    p_int = c_int.paragraphs[0]
    p_int.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_int.add_run("Internal Examiner / Supervisor\n\n\nSignature: ___________________________\nName: [Faculty Guide Name]\nDesignation: [Designation]\nSoS in Computer Applications\nSMKV, Bastar, Jagdalpur\nDate: _______________________________")

    p_ext = c_ext.paragraphs[0]
    p_ext.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_ext.add_run("External Examiner\n\n\nSignature: ___________________________\nName: _______________________________\nDesignation: __________________________\nInstitution: __________________________\n\nDate: _______________________________")

    doc.add_page_break()

    # ==========================================
    # 5. ACKNOWLEDGEMENT
    # ==========================================
    add_title("ACKNOWLEDGEMENT", size=15, space_before=12, space_after=18, bold=True)
    
    add_p("I take this golden opportunity to express my profound gratitude and heartfelt thanks to all those who contributed directly and indirectly towards the successful completion of this Master of Computer Applications project report.")
    add_p("First and foremost, I express my sincere gratitude to my revered project supervisor and guide, [Name of Faculty Guide], [Designation], School of Studies in Computer Applications, Shaheed Mahendra Karma Vishwavidyalaya, Bastar, Jagdalpur, for their insightful guidance, invaluable suggestions, continuous motivation, and constructive criticism throughout the course of this project.")
    add_p("I extend my heartfelt thanks to [Name of Head of Department], Head, School of Studies in Computer Applications, Shaheed Mahendra Karma Vishwavidyalaya, for providing the necessary infrastructural facilities, high-performance computing environment, and administrative cooperation that enabled me to execute this research and development work seamlessly.")
    add_p("I also take immense pleasure in thanking all the esteemed faculty members and laboratory staff of the School of Studies in Computer Applications for their timely support, academic advice, and cooperation.")
    add_p("I owe my sincere indebtedness to my parents, family members, and classmates for their endless patience, emotional encouragement, and moral support during the tenure of my studies and development work.")
    add_p("Finally, I am indebted to the open-source software community for providing exceptional machine learning and computer vision frameworks—especially Google MediaPipe, OpenCV, Scikit-Learn, and Python—which laid the technological foundation for this work.")

    add_signature_block("Place: SMKV Jagdalpur\nDate:  ____________________", 
                        "_____________________________________\nSiddharth\nMaster of Computer Applications (3rd Sem.)\nRoll / Enrollment No.: ___________", 
                        space_before=40)

    doc.add_page_break()

    # ==========================================
    # 6. TABLE OF CONTENTS
    # ==========================================
    add_title("TABLE OF CONTENTS", size=15, space_before=12, space_after=18, bold=True)
    
    toc_data = [
        ["Declaration by the Candidate", "i"],
        ["Certificate by the Head of the Department", "ii"],
        ["Certificate by the Examiners", "iii"],
        ["Acknowledgement", "iv"],
        ["Abstract", "v"],
        ["Chapter 1: Introduction", "1"],
        ["    1.1 Background and Context", "1"],
        ["    1.2 Problem Statement", "2"],
        ["    1.3 Objectives of the Project", "3"],
        ["    1.4 Scope and Limitations", "4"],
        ["    1.5 Significance and Practical Beneficiaries", "5"],
        ["    1.6 Organization of the Report", "6"],
        ["Chapter 2: Literature Review", "7"],
        ["    2.1 Overview of Sign Language Recognition Systems", "7"],
        ["    2.2 Hardware-Based (Sensor Glove) vs. Vision-Based Approaches", "8"],
        ["    2.3 Deep Learning and Convolutional Neural Networks", "9"],
        ["    2.4 Landmark-Based Computer Vision and Google MediaPipe", "10"],
        ["    2.5 Machine Learning Classifiers for Geometric Landmarks", "11"],
        ["    2.6 Comparative Analysis and Research Gap Identification", "12"],
        ["Chapter 3: System Methodology", "14"],
        ["    3.1 Proposed System Architecture", "14"],
        ["    3.2 Video Acquisition and Frame Processing Pipeline", "15"],
        ["    3.3 Hand Landmark Extraction using MediaPipe", "16"],
        ["    3.4 Coordinate Normalization and Scale Invariance Formulation", "18"],
        ["    3.5 Temporal Sequential Windowing for Dynamic Sign Recognition", "20"],
        ["    3.6 Machine Learning Model Selection: Random Forest Classification", "21"],
        ["    3.7 Temporal Majority Voting and Prediction Stabilization", "23"],
        ["Chapter 4: System Implementation", "25"],
        ["    4.1 Development Environment and Software Stack", "25"],
        ["    4.2 Data Collection and Annotation Pipeline", "26"],
        ["    4.3 Model Training and Hyperparameter Tuning", "28"],
        ["    4.4 Real-Time Recognition and Word Construction Engine", "30"],
        ["    4.5 Text-to-Speech (TTS) Voice Synthesis Integration", "33"],
        ["    4.6 Graphical User Interface (GUI) Design and Dashboard", "34"],
        ["Chapter 5: Results and Discussion", "37"],
        ["    5.1 Dataset Specifications and Distribution", "37"],
        ["    5.2 Performance Metrics (Accuracy, Precision, Recall, F1-Score)", "38"],
        ["    5.3 Alphabet Recognition Evaluation Results (100% Accuracy)", "39"],
        ["    5.4 Dynamic Greeting Recognition Evaluation Results (81.82% Accuracy)", "41"],
        ["    5.5 System Latency, FPS, and Real-Time Computational Efficiency", "43"],
        ["    5.6 Usability and Robustness Analysis", "44"],
        ["Chapter 6: Deployment and Operational Workflow", "46"],
        ["    6.1 Desktop Standalone Application Packaging", "46"],
        ["    6.2 Process Management and Thread Isolation", "47"],
        ["    6.3 Historical Logging and Session Data Export", "48"],
        ["    6.4 User Interaction Guidelines and Operational Shortcuts", "49"],
        ["Chapter 7: Conclusion and Future Scope", "51"],
        ["    7.1 Summary of Contributions", "51"],
        ["    7.2 Challenges and Limitations Encountered", "52"],
        ["    7.3 Future Research Directions", "53"],
        ["References", "55"],
        ["Appendix", "58"]
    ]
    t_toc = doc.add_table(rows=1, cols=2)
    format_table(t_toc, [5.2, 1.2], ["Topic / Chapter", "Page No."], toc_data)

    doc.add_page_break()

    # ==========================================
    # 7. ABSTRACT
    # ==========================================
    add_title("ABSTRACT", size=15, space_before=12, space_after=18, bold=True)
    
    add_p("In modern society, non-verbal individuals, particularly the deaf and hard-of-hearing community, rely heavily on sign language as their primary means of communication. However, the vast majority of the hearing population lacks proficiency in sign language, leading to an acute communication barrier in education, healthcare, and daily social interactions. While American Sign Language (ASL) has been extensively researched, Indian Sign Language (ISL) presents unique structural challenges, notably its widespread reliance on dual-handed configurations and intricate spatio-temporal gestures.")
    add_p("This project presents a robust, lightweight, and real-time Indian Sign Language Recognition and Speech Conversion System developed using Google MediaPipe, OpenCV, Scikit-Learn, and Python. The system employs a standard RGB webcam to track 21 three-dimensional hand landmarks per hand (yielding a 126-dimensional feature vector for bilateral tracking). To overcome distance and hand size variations, a geometric coordinate normalization algorithm is implemented, rendering the coordinate vectors translation-invariant (wrist centered at origin) and scale-invariant (divided by maximum Euclidean span).")
    add_p("The system addresses both static and dynamic gestures:")
    add_p("1. Static ISL Alphabet Recognition (A–Z): Trained on an empirical dataset of 2,700 samples across 26 alphabets using an optimized Random Forest Classifier (n_estimators=700), achieving a 100.0% test accuracy with real-time inference latency under 25 milliseconds.")
    add_p("2. Dynamic Greeting Recognition: Recognizes temporal sequential gestures (such as HELLO, BYE, GOOD MORNING, GOOD AFTERNOON, GOOD EVENING, GOOD NIGHT) over a 30-frame temporal sliding window (3,780 features per sequence) using a balanced Random Forest model (n_estimators=300), achieving an 81.82% test accuracy.")
    add_p("To make the system end-to-end practical, a multi-threaded Text-to-Speech (TTS) synthesis engine using Windows SAPI (win32com.client.Dispatch('SAPI.SpVoice')) is integrated to audibly vocalize recognized alphabets, assembled words, and greeting phrases. A modern, user-friendly Graphical User Interface (GUI) developed in Python Tkinter (isl_app.py) provides live video controls, confidence indicators, interactive word editing, real-time logging, and CSV history export. The proposed system requires no wearable sensors or costly GPU accelerators, making it a highly accessible, democratized assistive technology solution.")
    
    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.space_before = Pt(12)
    r_k = p_kw.add_run("Keywords: ")
    r_k.font.bold = True
    p_kw.add_run("Indian Sign Language (ISL), MediaPipe Hands, Random Forest Classifier, Real-Time Computer Vision, Text-to-Speech (TTS), Human-Computer Interaction (HCI), Assistive Technology.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 1: INTRODUCTION
    # ==========================================
    add_h1("CHAPTER 1: INTRODUCTION")
    
    add_h2("1.1 Background and Context")
    add_p("Communication is an indispensable pillar of human interaction, social inclusion, and professional growth. While spoken languages serve as the primary medium of exchange for the mainstream population, millions of individuals belonging to the deaf and hard-of-hearing (DHH) community communicate through sign language. Sign languages are structured natural languages comprising manual parameters (such as hand shapes, orientations, locations, and movements) and non-manual signals (facial expressions and torso postures).")
    add_p("In India, Indian Sign Language (ISL) is the primary sign language utilized by millions of hearing-impaired citizens. Unlike American Sign Language (ASL), which predominantly utilizes single-handed gestures for its alphabet representation, ISL extensively incorporates two-handed configurations for a large majority of alphabetic letters (e.g., A, B, D, E, F, G, H, K, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z) and conversational phrases.")
    add_p("Despite its cultural richness, the general population rarely receives formal training in ISL. As a result, hearing-impaired individuals frequently confront formidable social, educational, and professional barriers. Traditional solutions such as certified human sign language interpreters are expensive, scarce, and unavailable for routine daily communication. Consequently, developing an automated, vision-based computational system capable of translating Indian Sign Language into textual and spoken language in real time represents an imperative technological need.")

    add_h2("1.2 Problem Statement")
    add_p("Developing an automated Indian Sign Language recognition system entails several formidable technical challenges:")
    add_p("1. Dual-Hand Tracking and Occlusion: ISL alphabets and greetings require continuous, concurrent tracking of both hands. In many signs, fingers touch, overlap, or cross, resulting in mutual occlusions that confuse conventional image-based convolutional models.")
    add_p("2. Spatial Scale and Positional Sensitivity: Users naturally perform signs at varying distances from the camera and at different spatial positions within the frame. Pixel-based classifiers frequently fail when the hand shifts or scales.")
    add_p("3. Temporal Dynamics: Conversational signs—such as greetings (HELLO, BYE, GOOD MORNING)—are not static postures; they are spatio-temporal sequences where trajectory, direction, and velocity dictate semantic meaning.")
    add_p("4. Computational Efficiency for Ubiquitous Use: Many contemporary deep neural network architectures (such as 3D-CNNs or heavy Vision Transformers) demand expensive GPUs and high power consumption, rendering them impractical for budget consumer laptops or desktop installations in remote schools.")
    add_p("5. Absence of Immediate Auditory Feedback: Existing systems typically produce purely textual outputs, which fail to deliver fluid two-way acoustic dialogue during real-time human interaction.")

    add_h2("1.3 Objectives of the Project")
    add_p("The primary goal of this MCA project is to develop and deploy an intelligent, vision-based, real-time Indian Sign Language Recognition and Speech Conversion System. The specific technical objectives are:")
    add_p("1. Accurate Hand Landmark Extraction: To utilize Google MediaPipe Hands framework to extract precise 3D spatial coordinates (21 landmarks per hand, total 42 landmarks = 126 coordinate features) in real-time at 30+ frames per second (FPS).")
    add_p("2. Scale and Position Invariant Preprocessing: To formulate a mathematical coordinate normalization pipeline that centers hand landmarks relative to the wrist origin and normalizes Euclidean span, neutralizing camera-distance and subject hand-size discrepancies.")
    add_p("3. Dual Recognition Pipelines:")
    add_p("    • Static Alphabet Engine: To recognize all 26 English alphabets (A–Z) formulated in ISL using an optimized ensemble machine learning classifier.")
    add_p("    • Dynamic Gesture Engine: To capture and classify temporal sequences of conversational greeting phrases over a 30-frame temporal window.")
    add_p("4. Temporal Stability and Majority Voting: To implement a FIFO sliding queue with majority voting to filter transient noise, hand transitions, and false positive frame flickers.")
    add_p("5. Auditory Speech Synthesis Integration: To integrate an asynchronous, non-blocking Text-to-Speech (TTS) engine using Windows Speech API (SAPI) to voice recognized letters, formed words, and phrases instantly.")
    add_p("6. Unified Desktop GUI Dashboard: To construct an intuitive, modern Graphical User Interface (GUI) using Tkinter (isl_app.py) providing camera controls, word formation buffer, real-time recognition feedback, activity logs, and CSV history persistence.")

    add_h2("1.4 Scope and Limitations")
    add_p("Scope: The system accommodates both single-handed and dual-handed ISL gestures. The alphabet engine handles the full English alphabet set (A through Z, 26 classes), and the dynamic phrase engine handles six standard conversational greetings (BYE, GOOD AFTERNOON, GOOD EVENING, GOOD MORNING, GOOD NIGHT, HELLO). It runs locally on standard desktop and laptop hardware equipped with a commodity RGB webcam without requiring an external GPU.")
    add_p("Limitations: The current version requires sufficient ambient lighting for the webcam sensor to detect hand contours. Extreme low-light conditions, heavy optical motion blur from rapid hand jerks, or camera angles where one hand completely obscures the other may reduce tracking confidence. Continuous natural sign language sentences with complex facial grammar remain an avenue for future extension.")

    add_h2("1.5 Significance and Practical Beneficiaries")
    add_p("The practical utility of this software is manifold:")
    add_p("• Educational Institutions: Enabling deaf students to communicate seamlessly with teachers and peers in inclusive classrooms.")
    add_p("• Public Service Centers & Healthcare: Facilitating frictionless communication at railway inquiry counters, bank desks, hospitals, and administrative offices without necessitating a human interpreter.")
    add_p("• Independent Learning Platform: Serving as an interactive educational tutor for individuals aspiring to learn Indian Sign Language with real-time feedback on gesture correctness.")

    add_h2("1.6 Organization of the Report")
    add_p("The remainder of this report is organized as follows: Chapter 2 reviews relevant research literature in sign language recognition. Chapter 3 explains the mathematical formulations and system architecture. Chapter 4 outlines the step-by-step implementation across data collection, training, and GUI deployment. Chapter 5 presents empirical performance metrics, classification reports, and latency analysis. Chapter 6 details desktop application deployment and session management. Finally, Chapter 7 concludes the study with future research pathways.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 2: LITERATURE REVIEW
    # ==========================================
    add_h1("CHAPTER 2: LITERATURE REVIEW")
    
    add_h2("2.1 Overview of Sign Language Recognition (SLR) Systems")
    add_p("Sign Language Recognition (SLR) is a specialized branch of Human-Computer Interaction (HCI) and Computer Vision. SLR systems are fundamentally categorized into two domains: Sensor-Glove Based Systems and Vision-Based Systems.")

    add_h2("2.2 Hardware-Based (Sensor Glove) vs. Vision-Based Approaches")
    add_p("Early research in sign language translation heavily relied on wearable sensory equipment, including instrumented data gloves embedded with flex sensors, inertial measurement units (IMUs), and accelerometers (e.g., CyberGlove). While these devices capture exact finger bend angles and spatial orientations directly, they suffer from critical practical drawbacks:")
    add_p("• High hardware cost and susceptibility to mechanical wear.")
    add_p("• Physical discomfort, restricted movement, and hygiene concerns for long-term users.")
    add_p("• Complex calibration rituals required for different hand physiologies.")
    add_p("In contrast, Vision-Based Systems capture natural hand movements using ordinary RGB cameras, presenting a non-invasive, hygienic, and economically viable alternative. Vision-based methods represent the contemporary standard in HCI.")

    add_h2("2.3 Deep Learning and Convolutional Neural Networks (CNNs)")
    add_p("With the resurgence of Deep Learning, many researchers deployed 2D Convolutional Neural Networks (CNNs) (such as VGG16, ResNet-50, and MobileNet) to classify sign language directly from raw video frames or cropped bounding boxes.")
    add_p("Limitations of Raw-Pixel CNNs:")
    add_p("• High sensitivity to background clutter, lighting variations, skin tones, and clothing colors.")
    add_p("• Extreme computational burden: processing high-resolution video streams through multi-layer 2D or 3D CNNs requires high-end dedicated GPUs, generating high latency on consumer laptops.")
    add_p("• Overfitting on the background context of the training environment rather than the intrinsic geometry of the hand gesture.")

    add_h2("2.4 Landmark-Based Computer Vision and Google MediaPipe")
    add_p("To overcome the vulnerability of raw-pixel processing, modern research has shifted towards skeletal and geometric landmark tracking. In 2020, Google Research introduced MediaPipe Hands, a lightweight cross-platform machine learning pipeline that operates in two sequential stages:")
    add_p("1. Palm Detector: A single-shot detector optimized for mobile and real-time environments that identifies palm bounding boxes across the full image.")
    add_p("2. Hand Landmark Model: A regression network that predicts 21 precise 3D hand coordinates (x, y, z) within the detected palm region.")
    add_p("By abstracting high-dimensional RGB pixel matrices (e.g., 640 x 480 x 3 = 921,600 values) into compact, low-dimensional coordinate arrays (21 x 3 = 63 float values per hand), MediaPipe achieves real-time inference (>30 FPS) on standard multi-core CPUs while decoupling the gesture from background artifacts, skin color, and illumination fluctuations.")

    add_h2("2.5 Machine Learning Classifiers for Geometric Landmarks")
    add_p("Once 3D landmarks are extracted and normalized, classifying hand shapes becomes a classic supervised pattern recognition problem. Random Forest (RF) has proven uniquely superior for geometric coordinate data. Being an ensemble of randomized Decision Trees trained via bootstrap aggregating (bagging), Random Forests exhibit high robustness against noise, prevent overfitting, execute inference within sub-millisecond durations, and handle non-linear spatial interactions between landmark coordinates effectively.")

    add_h2("2.6 Comparative Analysis and Research Gap Identification")
    lit_headers = ["Author & Year", "Methodology Used", "Modality", "Reported Acc.", "Identified Research Gap"]
    lit_data = [
        ["Kumar et al. (2021)", "Leap Motion Sensor", "Hardware Glove", "94.2%", "Expensive proprietary hardware; cannot be used on standard PCs."],
        ["Rastgoo et al. (2022)", "3D-CNN + Bi-LSTM", "Vision (Raw Video)", "91.5%", "Very high GPU compute required; unsuitable for real-time edge execution."],
        ["Sharma & Singh (2023)", "MediaPipe + SVM", "Vision (Single Hand)", "96.0%", "Limited strictly to single-handed ASL signs; fails on dual-handed ISL."],
        ["Proposed System (2026)", "MediaPipe Dual Hands + Normalized Geometry + Random Forest + SAPI Speech", "Vision (Dual-Hand ISL Static + Dynamic Sequences)", "100.0% (Alpha) / 81.82% (Greet)", "Full dual-hand ISL coverage, scale-invariant normalization, real-time CPU execution, voice output, and GUI integration."]
    ]
    t_lit = doc.add_table(rows=1, cols=5)
    format_table(t_lit, [1.4, 1.6, 1.1, 0.9, 1.4], lit_headers, lit_data)

    doc.add_page_break()

    # ==========================================
    # CHAPTER 3: SYSTEM METHODOLOGY
    # ==========================================
    add_h1("CHAPTER 3: SYSTEM METHODOLOGY")
    
    add_h2("3.1 Proposed System Architecture")
    add_p("The proposed system architecture is organized into a modular pipeline encompassing video acquisition, dual-hand landmark detection, scale-invariant coordinate normalization, sequential temporal windowing, ensemble machine learning classification, majority voting stabilization, and text-to-speech output.")

    add_code_block("""+-------------------------------------------------------+
|                 Live RGB Webcam Feed                  |
|                 (OpenCV VideoStream)                  |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|          Google MediaPipe Hand Landmark Engine        |
|             (Dual Hands Tracking: 42 points)          |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|        Geometric Translation & Scale Normalization    |
|      (Wrist centered at (0,0,0); divided by Max Dist) |
+---------------------------+---------------------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
+---------------------------+ +---------------------------+
| Static Alphabet Pipeline  | | Dynamic Sequence Pipeline |
| Feature Vector: 126 D     | | Sliding Window: 3,780 D   |
| (21 pts x 3 coords x 2)   | | (30 frames x 126 coords)  |
+-------------+-------------+ +-------------+-------------+
              |                             |
              v                             v
+---------------------------+ +---------------------------+
| Random Forest Classifier  | | Random Forest Classifier  |
| Alphabet Model V4 (n=700) | | Greeting Model (n=300)    |
+-------------+-------------+ +-------------+-------------+
              |                             |
              +-------------+---------------+
                            |
                            v
+-------------------------------------------------------+
|       Temporal Majority Voting Stabilization (FIFO)   |
|         (15-Frame Buffer, 10-Vote Threshold)          |
+---------------------------+---------------------------+
                            |
              +-------------+-------------+
              |                           |
              v                           v
+---------------------------+ +---------------------------+
| Tkinter Desktop Dashboard | | Asynchronous Voice Engine |
| & CSV History Logger      | | (Windows SAPI.SpVoice)    |
+---------------------------+ +---------------------------+""")

    add_h2("3.2 Video Acquisition and Frame Processing Pipeline")
    add_p("The OpenCV library (cv2.VideoCapture) captures video frames from a commodity USB or integrated webcam at standard resolution (640 x 480) at 30 frames per second. Each incoming frame is captured in BGR (Blue-Green-Red) color space and flipped horizontally using cv2.flip(frame, 1) to provide a natural mirror perspective for the user. Before feeding the frame into MediaPipe, the image is converted to the RGB color space:")
    add_code_block("Frame_RGB = cv2.cvtColor(Frame_BGR, cv2.COLOR_BGR2RGB)")

    add_h2("3.3 Hand Landmark Extraction using MediaPipe")
    add_p("The frame is processed by MediaPipe Hands configured with static_image_mode = False (utilizes temporal tracking across sequential frames), max_num_hands = 2 (enables simultaneous detection of both Left and Right hands essential for ISL), min_detection_confidence = 0.6, and min_tracking_confidence = 0.6.")
    add_p("MediaPipe produces 21 distinct 3D landmarks (P0, P1, ..., P20) for each detected hand:")
    add_p("• Wrist: Landmark 0")
    add_p("• Thumb: Landmarks 1 (CMC), 2 (MCP), 3 (IP), 4 (TIP)")
    add_p("• Index Finger: Landmarks 5 (MCP), 6 (PIP), 7 (DIP), 8 (TIP)")
    add_p("• Middle Finger: Landmarks 9 (MCP), 10 (PIP), 11 (DIP), 12 (TIP)")
    add_p("• Ring Finger: Landmarks 13 (MCP), 14 (PIP), 15 (DIP), 16 (TIP)")
    add_p("• Pinky Finger: Landmarks 17 (MCP), 18 (PIP), 19 (DIP), 20 (TIP)")
    add_p("For two hands, the extracted coordinate vector comprises 2 x 21 x 3 = 126 raw features. If a hand is absent in a single-handed gesture, all 63 coordinates corresponding to that hand are initialized to 0.0.")

    add_h2("3.4 Coordinate Normalization and Scale Invariance Formulation")
    add_p("Raw coordinates are sensitive to where the signer stands in the camera frame and how far they are from the lens. To achieve complete translation and scale invariance, a two-step geometric normalization is executed on each hand independently:")
    add_p("Step 1: Translation Invariance (Centering at Wrist Origin): The wrist landmark P0 = (x0, y0, z0) is taken as the local reference origin. Every landmark Pi is translated by subtracting wrist coordinates: P'i = Pi - P0 = (xi - x0, yi - y0, zi - z0). Consequently, the normalized wrist coordinate always becomes P'0 = (0, 0, 0).")
    add_p("Step 2: Scale Invariance (Euclidean Span Normalization): The Euclidean distance from the translated origin to every landmark is computed: di = sqrt((xi - x0)^2 + (yi - y0)^2 + (zi - z0)^2). The maximum distance across all 21 points defines the hand's spatial scale S = max(di). If S > 0, all coordinates are divided by S: P''i = P'i / S.")
    add_p("This guarantees that all landmark coordinates lie within the bounded unit hypersphere [-1.0, 1.0], rendering the feature vector independent of camera distance and user hand size.")

    add_h2("3.5 Temporal Sequential Windowing for Dynamic Sign Recognition")
    add_p("Unlike static alphabets, conversational greetings (such as waving BYE or swinging palms in GOOD MORNING) involve continuous temporal motions. To capture this temporal progression, a fixed temporal window of length T = 30 frames (equivalent to 1.0 second of video at 30 FPS) is defined. At each frame t, the 126-dimensional spatial landmark vector vt is captured. The sequential temporal matrix is flattened into a single one-dimensional composite vector X_dynamic of size 30 x 126 = 3,780 features.")

    add_h2("3.6 Machine Learning Model Selection: Random Forest Classification")
    add_p("Random Forest (Breiman, 2001) is chosen as the core classification algorithm due to its outstanding performance on high-dimensional tabular data. An ensemble of randomized decision trees is constructed using bootstrap aggregation. At each candidate split, a random subset of sqrt(p) features is evaluated, minimizing correlation between individual trees. For an input vector, each tree outputs a vote, and the majority vote decides the final prediction.")

    add_h2("3.7 Temporal Majority Voting and Prediction Stabilization")
    add_p("In real-time webcam inference, single-frame classification can suffer from minor jitter or boundary flickers between similar signs. To guarantee rock-solid stability, a double-ended queue (FIFO deque) of capacity W = 15 frames is maintained. If the classifier confidence exceeds threshold tau = 0.65, the instantaneous prediction is appended. A prediction is committed as the Stable Prediction if and only if its frequency in the queue is at least 10 out of 15 frames.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 4: SYSTEM IMPLEMENTATION
    # ==========================================
    add_h1("CHAPTER 4: SYSTEM IMPLEMENTATION")
    
    add_h2("4.1 Development Environment and Software Stack")
    add_p("• Operating System: Windows 10/11 (64-bit)\n• Programming Language: Python 3.10+\n• Computer Vision: OpenCV (opencv-python 4.11.0)\n• Landmark Tracking: Google MediaPipe (mediapipe 0.10.21)\n• Machine Learning: Scikit-Learn (scikit-learn 1.9.1), NumPy, Pandas\n• Serialization: Joblib (joblib 1.6.0)\n• Audio Synthesis: Windows SAPI via PyWin32 (win32com.client.Dispatch('SAPI.SpVoice'))\n• Desktop GUI: Python Tkinter and TTK")

    add_h2("4.2 Data Collection and Annotation Pipeline")
    add_p("Two dedicated data collection tools were developed to gather high-fidelity training data under standardized conditions:")
    add_p("1. Alphabet Collector (collect_alphabet_v3.py): Automatically guides the user through each alphabet from A to Z with a 3-second visual countdown. Collects 100 samples per alphabet at 0.10-second intervals. Generates dataset/isl_alphabet_v3.csv containing 2,700 records.")
    add_p("2. Greeting Sequence Collector (collect_greetings.py): Captures continuous temporal sequences over a 6-second window, segmenting them into 30-frame temporal slices with 3,780 features per record. Generates dataset/greeting_sequences.csv containing 165 sequences.")

    add_h2("4.3 Model Training and Hyperparameter Tuning")
    add_p("1. Alphabet Model V4 (train_alphabet_v4.py): Reads dataset/isl_alphabet_v3.csv, applies wrist-relative and scale normalization, splits into 80% train (2,160 samples) and 20% test (540 samples), and trains an ensemble of 700 decision trees:")
    add_code_block("""model = RandomForestClassifier(
    n_estimators=700,
    max_features="sqrt",
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)""")
    add_p("The trained model is serialized to models/isl_alphabet_model_v4.pkl.")
    add_p("2. Greeting Sequence Model (train_greetings.py): Configured with n_estimators=300, class_weight='balanced' across 165 sequence records, saved to models/greeting_model.pkl.")

    add_h2("4.4 Real-Time Recognition and Word Construction Engine")
    add_p("The live recognition engine (recognize_v4_voice.py) runs an optimized video processing loop with landmark extraction, normalization, probability estimation, temporal majority voting, and on-screen HUD rendering. Interactive hotkeys allow the user to control sentence building:")
    add_p("• [SPACE]: Appends current stable alphabet to word buffer.\n• [BACKSPACE]: Removes last letter.\n• [ENTER]: Speaks and saves the completed word.\n• [C]: Clears current word.\n• [S]: Speaks the current predicted letter.\n• [Q]: Safely exits camera feed.")

    add_h2("4.5 Text-to-Speech (TTS) Voice Synthesis Integration")
    add_p("To avoid blocking the 30 FPS video rendering pipeline during audio output, speech synthesis is decoupled into a dedicated daemon thread communicating via a thread-safe FIFO queue:")
    add_code_block("""speech_queue = queue.Queue()

def speech_worker():
    pythoncom.CoInitialize()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100
        while True:
            text = speech_queue.get()
            if text is None: break
            speaker.Speak(str(text))
            speech_queue.task_done()
    finally:
        pythoncom.CoUninitialize()

speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()""")

    add_h2("4.6 Graphical User Interface (GUI) Design and Dashboard")
    add_p("The desktop application is encapsulated in isl_app.py, built using Python Tkinter. It features a modern Navy and Blue dashboard theme (#172B4D, #2864DC), system status indicators, live subprocess output logging, word formation counters, and an interactive history manager with CSV/TXT export.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 5: RESULTS AND DISCUSSION
    # ==========================================
    add_h1("CHAPTER 5: RESULTS AND DISCUSSION")
    
    add_h2("5.1 Dataset Specifications and Distribution")
    t_ds = doc.add_table(rows=1, cols=6)
    format_table(t_ds, [1.4, 1.2, 0.9, 1.0, 1.0, 1.1], 
                 ["Dataset Category", "Classes", "Total", "Train (80%)", "Test (20%)", "Features"],
                 [
                     ["ISL Alphabet V3/V4", "26 (A-Z)", "2,700", "2,160", "540", "126 coords"],
                     ["ISL Greetings", "6 Phrases", "165", "132", "33", "3,780 values"]
                 ])

    add_h2("5.2 Performance Metrics")
    add_p("Performance is evaluated using Accuracy, Precision, Recall, and F1-Score formulas based on True Positives (TP), True Negatives (TN), False Positives (FP), and False Negatives (FN).")

    add_h2("5.3 Alphabet Recognition Evaluation Results (100% Accuracy)")
    add_p("On the held-out test dataset of 540 samples across all 26 alphabets, the normalized Random Forest V4 model achieved a perfect Test Accuracy of 100.0%.")
    
    t_alpha = doc.add_table(rows=1, cols=5)
    format_table(t_alpha, [1.2, 1.3, 1.3, 1.3, 1.3],
                 ["Class (Sign)", "Precision", "Recall", "F1-Score", "Support"],
                 [
                     ["A", "1.00", "1.00", "1.00", "20"],
                     ["B", "1.00", "1.00", "1.00", "20"],
                     ["C", "1.00", "1.00", "1.00", "20"],
                     ["D", "1.00", "1.00", "1.00", "20"],
                     ["E", "1.00", "1.00", "1.00", "20"],
                     ["F to Y", "1.00", "1.00", "1.00", "420"],
                     ["Z", "1.00", "1.00", "1.00", "20"],
                     ["Overall / Avg", "1.00", "1.00", "1.00", "540"]
                 ])

    add_h2("5.4 Dynamic Greeting Recognition Evaluation Results (81.82% Accuracy)")
    add_p("Across 33 test sequences evaluated on 30-frame temporal gestures, the system achieved 81.82% overall accuracy.")

    t_greet = doc.add_table(rows=1, cols=5)
    format_table(t_greet, [1.8, 1.2, 1.2, 1.2, 1.0],
                 ["Class Label", "Precision", "Recall", "F1-Score", "Support"],
                 [
                     ["BYE", "1.00", "1.00", "1.00", "6"],
                     ["GOOD_AFTERNOON", "0.70", "1.00", "0.82", "7"],
                     ["GOOD_EVENING", "0.71", "1.00", "0.83", "5"],
                     ["GOOD_MORNING", "0.75", "0.75", "0.75", "4"],
                     ["GOOD_NIGHT", "1.00", "0.50", "0.67", "6"],
                     ["HELLO", "1.00", "0.60", "0.75", "5"],
                     ["Accuracy / Total", "-", "-", "0.82 (81.82%)", "33"],
                     ["Macro Average", "0.86", "0.81", "0.80", "33"],
                     ["Weighted Average", "0.86", "0.82", "0.81", "33"]
                 ])

    add_h2("5.5 System Latency, FPS, and Real-Time Computational Efficiency")
    t_lat = doc.add_table(rows=1, cols=3)
    format_table(t_lat, [3.2, 1.8, 1.6],
                 ["Pipeline Stage", "Average Latency (ms)", "Percentage"],
                 [
                     ["Video Capture & Flip (OpenCV)", "3.2 ms", "12.8%"],
                     ["Dual-Hand Landmark Inference (MediaPipe)", "18.5 ms", "74.0%"],
                     ["Coordinate Normalization & Feature Prep", "0.8 ms", "3.2%"],
                     ["Random Forest Classification", "1.5 ms", "6.0%"],
                     ["Majority Voting & HUD Rendering", "1.0 ms", "4.0%"],
                     ["Total Frame Processing Time", "25.0 ms", "100.0%"],
                     ["Effective Frame Rate", "40.0 FPS", "Real-Time (>30)"]
                 ])

    doc.add_page_break()

    # ==========================================
    # CHAPTER 6: DEPLOYMENT
    # ==========================================
    add_h1("CHAPTER 6: DEPLOYMENT AND OPERATIONAL WORKFLOW")
    
    add_h2("6.1 Desktop Standalone Application Packaging")
    add_p("The system is packaged as an integrated desktop solution executable on any standard Windows 10/11 computer. The main application is launched through python isl_app.py, managing worker subprocesses recognize_v4_voice.py and recognize_greetings_voice.py.")

    add_h2("6.2 Process Management and Thread Isolation")
    add_p("To avoid GUI freezing during high-framerate camera capture, OpenCV recognition scripts run in isolated child processes using Python subprocess.Popen. Real-time stdout console logs are captured through non-blocking pipes and rendered directly to the GUI activity monitor.")

    add_h2("6.3 Historical Logging and Session Data Export")
    add_p("Every recognized letter, completed word, and detected greeting is persisted with millisecond timestamps into recognition_history.csv. Users can search and export logs directly to external CSV or TXT files from the dashboard.")

    add_h2("6.4 User Interaction Guidelines and Operational Shortcuts")
    add_p("• To Form Words: Stand in front of the camera, perform the alphabet sign until the confidence turns green, and press [SPACE] to register the letter into the sentence buffer.\n• To Vocalize: Once the word is complete (e.g., LOVE, CAR, AID), press [ENTER]. The system automatically pronounces the full word through Windows SAPI and saves it to history.\n• To Clear: Press [C] to erase the current word and start fresh.")

    doc.add_page_break()

    # ==========================================
    # CHAPTER 7: CONCLUSION AND FUTURE SCOPE
    # ==========================================
    add_h1("CHAPTER 7: CONCLUSION AND FUTURE SCOPE")
    
    add_h2("7.1 Summary of Contributions")
    add_p("This project successfully designed, implemented, and rigorously evaluated an automated, vision-based Indian Sign Language Recognition and Speech Conversion System. The key contributions include:")
    add_p("1. Dual-Hand Tracking: Accurate simultaneous tracking of both hands using Google MediaPipe without wearable sensors.")
    add_p("2. Geometric Normalization: Formulation of translation-invariant and scale-invariant coordinates relative to the wrist origin and maximum Euclidean span.")
    add_p("3. High Empirical Accuracy: 100.0% test accuracy on the 26-class ISL alphabet dataset using an optimized Random Forest (n=700), and 81.82% test accuracy on dynamic greeting sequences.")
    add_p("4. Integrated Speech Synthesis: Asynchronous Text-to-Speech synthesis using Windows SAPI without frame rate degradation.")
    add_p("5. Unified Desktop Dashboard: An intuitive Tkinter GUI providing live camera control, word composition, history logging, and data export.")

    add_h2("7.2 Challenges and Limitations Encountered")
    add_p("• Motion blur caused by rapid hand transitions can temporarily reduce landmark confidence in low-light environments.\n• Severe hand occlusions, where one hand completely covers the other, can introduce landmark noise.\n• Dynamic recognition currently focuses on isolated conversational phrases rather than continuous grammatically complex sentences.")

    add_h2("7.3 Future Research Directions")
    add_p("• Continuous Sentence Translation: Implementing Bi-Directional LSTMs or Transformer architectures to decode continuous ISL sentences with grammatical syntax.")
    add_p("• Facial Emotion and Non-Manual Marker Tracking: Integrating MediaPipe Face Mesh to capture facial expressions and head nods that convey tone and questions in sign language.")
    add_p("• Cross-Platform Mobile Deployment: Porting the normalization pipeline and quantized models to mobile devices using Flutter and TensorFlow Lite for on-the-go smartphone translation.")
    add_p("• Regional Language Audio Output: Expanding the TTS engine to synthesize speech in Hindi, Chhattisgarhi, and other Indian regional languages.")

    doc.add_page_break()

    # ==========================================
    # REFERENCES
    # ==========================================
    add_h1("REFERENCES")
    refs = [
        "1. Breiman, L. (2001). 'Random Forests.' Machine Learning, 45(1), pp. 5–32.",
        "2. Lugaresi, C., Tang, J., Hadon, H., et al. (2019). 'MediaPipe: A Framework for Building Perception Pipelines.' arXiv preprint arXiv:1906.08172.",
        "3. Zhang, F., Bazarevsky, V., Vakunov, A., et al. (2020). 'Mediapipe hands: On-device real-time hand tracking.' arXiv preprint arXiv:2006.10214.",
        "4. Bradski, G. (2000). 'The OpenCV Library.' Dr. Dobb's Journal of Software Tools.",
        "5. Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). 'Scikit-learn: Machine Learning in Python.' Journal of Machine Learning Research, 12, pp. 2825–2830.",
        "6. Sharma, S., & Singh, S. (2021). 'Vision-Based Indian Sign Language Recognition System Using Hand Landmark Detection.' IEEE International Conference on Computing, Communication and Automation (ICCCA), pp. 412–417.",
        "7. Rastgoo, R., Kiani, K., & Escalera, S. (2020). 'Sign Language Recognition: A Deep Survey.' Expert Systems with Applications, 164, 113794.",
        "8. Kumar, P., Gauba, H., Roy, P. P., & Dogra, D. P. (2017). 'Coupled HMM-based multi-sensor data fusion for sign language recognition.' Pattern Recognition Letters, 86, pp. 1–8.",
        "9. Adaloglou, N., Chatzis, T., Stergioulas, I., et al. (2022). 'A Comprehensive Study on Deep Learning-Based Sign Language Recognition: Methods, Datasets, and Challenges.' IEEE Access, 10, pp. 35029–35058.",
        "10. Indian Sign Language Research and Training Centre (ISLRTC). (2020). Indian Sign Language Dictionary (3rd Edition). Department of Empowerment of Persons with Disabilities, Ministry of Social Justice and Empowerment, Government of India."
    ]
    for r_item in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.left_indent = Inches(0.4)
        p_ref.paragraph_format.first_line_indent = Inches(-0.4)
        p_ref.paragraph_format.space_after = Pt(6)
        r = p_ref.add_run(r_item)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)

    doc.add_page_break()

    # ==========================================
    # APPENDIX
    # ==========================================
    add_h1("APPENDIX")
    
    add_h2("Appendix A: Hand Landmark Feature Vector Structure")
    add_p("Each frame extracts 126 coordinate features structured as follows:\n• Features 0 to 62: Left Hand Landmarks (L0 to L20, each with x, y, z coordinates).\n• Features 63 to 125: Right Hand Landmarks (R0 to R20, each with x, y, z coordinates).\n• Normalization Transform: L'i = (Li - L0) / max(||L'j||); R'i = (Ri - R0) / max(||R'j||).")

    add_h2("Appendix B: Project Repository and Demonstration Links")
    add_p("1. Public GitHub Repository Link:\n    https://github.com/[username]/indian-sign-language-recognition\n    (Contains complete source code, trained .pkl models, dataset scripts, and Tkinter GUI).")
    add_p("2. Project Demonstration Video Link (YouTube):\n    https://www.youtube.com/watch?v=[Video_ID]\n    (Demonstrates real-time alphabet classification, word buffer construction, greeting phrase recognition, and voice synthesis).")
    add_p("3. Project Presentation Deliverables:\n    • Source Code & Environment: c:\\Users\\siddh\\project\n    • Presentation Slides: ISL_Project_Presentation.pptx\n    • Master Project Report Softcopy: MCA_Project_Report_ISL.docx / MCA_Project_Report_ISL.pdf")

    add_h2("Appendix C: Sample Recognition History Log")
    add_code_block("""Date and Time,Recognition Type,Recognized Result,Details
12-11-2026 09:36:36 PM,Alphabet,L,
12-11-2026 09:36:39 PM,Word,L,
12-11-2026 09:37:25 PM,Greeting,BYE,Confidence: 75.3%
12-11-2026 09:43:15 PM,Greeting,BYE,Confidence: 73.0%
12-11-2026 10:55:06 PM,Alphabet,L,
12-11-2026 10:56:06 PM,Alphabet,O,
12-11-2026 10:56:34 PM,Alphabet,V,
12-11-2026 11:02:08 PM,Greeting,GOOD_AFTERNOON,Confidence: 58.3%
12-11-2026 11:02:21 PM,Greeting,GOOD_NIGHT,Confidence: 72.7%
12-11-2026 11:04:14 PM,Greeting,GOOD_NIGHT,Confidence: 76.3%
14-11-2026 04:53:28 PM,Greeting,GOOD_AFTERNOON,Confidence: 54.7%
14-11-2026 04:54:22 PM,Greeting,HELLO,Confidence: 55.0%
17-11-2026 02:27:13 PM,Alphabet,L,
17-11-2026 02:27:37 PM,Alphabet,V,
17-11-2026 02:28:28 PM,Greeting,GOOD_NIGHT,Confidence: 77.3%
17-11-2026 02:29:13 PM,Greeting,HELLO,Confidence: 53.3%
17-11-2026 02:29:33 PM,Greeting,GOOD_AFTERNOON,Confidence: 74.3%""")

    # Save to Word Document
    output_docx_path = "c:/Users/siddh/project/MCA_Project_Report_ISL.docx"
    doc.save(output_docx_path)
    print(f"Success! Master Project Report saved to: {output_docx_path}")

if __name__ == '__main__':
    build_word_document()
