import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create():
    doc = docx.Document()
    p = doc.add_paragraph()
    r = p.add_run('STUDENT RECORDS (TABLE)')
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.font.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ['Roll No', 'Student Name', 'Course', 'Marks']
    data = [
        ['101', 'Aman Sharma', 'MCA', '85.50'],
        ['102', 'Pooja Verma', 'MCA', '91.00'],
        ['103', 'Rahul Patel', 'BCA', '78.50'],
        ['104', 'Sneha Mishra', 'MCA', '88.00']
    ]

    tblPr = table._tbl.tblPr
    borders = parse_xml(f'''
        <w:tblBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="8" w:space="0" w:color="172B4D"/>
            <w:bottom w:val="single" w:sz="8" w:space="0" w:color="172B4D"/>
            <w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            <w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            <w:left w:val="single" w:sz="8" w:space="0" w:color="172B4D"/>
            <w:right w:val="single" w:sz="8" w:space="0" w:color="172B4D"/>
        </w:tblBorders>
    ''')
    tblPr.append(borders)

    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="172B4D"/>')
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row in enumerate(data):
        row_cells = table.add_row().cells
        bg = 'FFFFFF' if r_idx % 2 == 0 else 'F4F6F9'
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = val
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg}"/>')
            row_cells[c_idx]._tc.get_or_add_tcPr().append(shd)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)

    col_widths = [1.2, 2.5, 1.5, 1.2]
    for row in table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = Inches(w)

    doc.save('c:/Users/siddh/project/Student_Table.docx')
    print('Student_Table.docx generated successfully!')

if __name__ == '__main__':
    create()
