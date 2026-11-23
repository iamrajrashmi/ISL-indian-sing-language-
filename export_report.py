import re
import html

def generate_html_report():
    with open('c:/Users/siddh/project/MCA_Project_Report_ISL.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    html_parts = []
    html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MCA Project Report - Real-Time Indian Sign Language Recognition</title>
<style>
    @page {
        size: A4;
        margin: 25mm 20mm 25mm 25mm;
    }
    body {
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #111;
        margin: 0 auto;
        padding: 40px;
        max-width: 850px;
        background: #fff;
    }
    h1 {
        font-size: 16pt;
        font-weight: bold;
        text-align: center;
        text-transform: uppercase;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    h2 {
        font-size: 14pt;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 12px;
    }
    h3 {
        font-size: 12pt;
        font-weight: bold;
        text-align: left;
        margin-top: 18px;
        margin-bottom: 8px;
    }
    h4 {
        font-size: 12pt;
        font-weight: bold;
        font-style: italic;
        text-align: left;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    p, li {
        text-align: justify;
        font-size: 12pt;
        margin-bottom: 8px;
    }
    .page-break {
        page-break-before: always;
        break-before: page;
        margin-top: 40px;
        border-top: 1px dashed #ccc;
        padding-top: 20px;
    }
    @media print {
        .page-break {
            border-top: none;
            padding-top: 0;
        }
        body {
            padding: 0;
            max-width: 100%;
        }
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 11pt;
    }
    th, td {
        border: 1px solid #444;
        padding: 6px 10px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    code {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 10.5pt;
    }
    pre {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #f8f9fa;
        padding: 12px;
        border: 1px solid #ccc;
        border-radius: 4px;
        overflow-x: auto;
        white-space: pre-wrap;
        font-size: 10pt;
        line-height: 1.3;
    }
    .center-block {
        text-align: center;
    }
    .univ-logo {
        display: block;
        margin: 10px auto;
        max-width: 150px;
    }
</style>
</head>
<body>
''')

    in_code = False
    in_table = False

    for line in lines:
        raw = line.rstrip('\r\n')

        if raw.strip().startswith('```'):
            if in_code:
                html_parts.append('</pre>\n')
                in_code = False
            else:
                html_parts.append('<pre>')
                in_code = True
            continue

        if in_code:
            html_parts.append(html.escape(raw) + '\n')
            continue

        if raw.strip() in ['\\newpage', '---']:
            if in_table:
                html_parts.append('</table>\n')
                in_table = False
            html_parts.append('<div class="page-break"></div>\n')
            continue

        # Tables
        if raw.strip().startswith('|') and raw.strip().endswith('|'):
            parts = [p.strip() for p in raw.strip()[1:-1].split('|')]
            if all(re.match(r'^:?-+:?$', p) for p in parts):
                continue
            if not in_table:
                html_parts.append('<table>\n')
                in_table = True
                html_parts.append('<tr>' + ''.join(f'<th>{p}</th>' for p in parts) + '</tr>\n')
            else:
                html_parts.append('<tr>' + ''.join(f'<td>{p}</td>' for p in parts) + '</tr>\n')
            continue
        else:
            if in_table:
                html_parts.append('</table>\n')
                in_table = False

        if raw.startswith('# '):
            html_parts.append(f'<h1>{raw[2:].strip()}</h1>\n')
        elif raw.startswith('## '):
            html_parts.append(f'<h2>{raw[3:].strip()}</h2>\n')
        elif raw.startswith('### '):
            html_parts.append(f'<h3>{raw[4:].strip()}</h3>\n')
        elif raw.startswith('#### '):
            html_parts.append(f'<h4>{raw[5:].strip()}</h4>\n')
        elif raw.strip() == '':
            html_parts.append('<br/>\n')
        else:
            txt = html.escape(raw)
            txt = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', txt)
            txt = re.sub(r'\*(.*?)\*', r'<em>\1</em>', txt)
            txt = re.sub(r'`(.*?)`', r'<code>\1</code>', txt)
            html_parts.append(f'<p>{txt}</p>\n')

    if in_table:
        html_parts.append('</table>\n')
    if in_code:
        html_parts.append('</pre>\n')

    html_parts.append('</body>\n</html>')

    with open('c:/Users/siddh/project/MCA_Project_Report_ISL.html', 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))

    print("Success: Generated MCA_Project_Report_ISL.html")

if __name__ == '__main__':
    generate_html_report()
