"""Typeset the revised report: PDF, HTML and Word from the editable Markdown.

Adapted from the first version's build_paper.py. Requires matplotlib, Pillow,
reportlab and python-docx. Fonts are the Windows Times New Roman and Arial files.
"""
from pathlib import Path
import sys, re, json, html
P = Path(__file__).resolve().parents[1]
for extra in (P.parent / 'Paper/.work/deps', P.parent / '.work/deps'):
    if extra.exists():
        sys.path.insert(0, str(extra))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether

NAME = 'SPHEREx_Project_Report_Revised'
TITLE = 'Seeing real change in SPHEREx sky images'
FONT = Path('C:/Windows/Fonts')
for name, file in [('Body', 'times.ttf'), ('BodyB', 'timesbd.ttf'), ('BodyI', 'timesi.ttf'), ('BodyBI', 'timesbi.ttf'),
                   ('Sans', 'arial.ttf'), ('SansB', 'arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT / file)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyB', italic='BodyI', boldItalic='BodyBI')
pdfmetrics.registerFontFamily('Sans', normal='Sans', bold='SansB', italic='Sans', boldItalic='SansB')
width = A4[0] - 100
ST = {
    'body': ParagraphStyle('body', fontName='Body', fontSize=11, leading=14.6, spaceAfter=8),
    'title': ParagraphStyle('title', fontName='BodyB', fontSize=23, leading=27, spaceAfter=11),
    'sub': ParagraphStyle('sub', fontName='BodyI', fontSize=12, leading=16, spaceAfter=9),
    'meta': ParagraphStyle('meta', fontName='Sans', fontSize=8.5, leading=12, spaceAfter=13),
    'h2': ParagraphStyle('h2', fontName='BodyB', fontSize=15, leading=19, spaceBefore=14, spaceAfter=8, keepWithNext=True),
    'h3': ParagraphStyle('h3', fontName='BodyB', fontSize=12, leading=16, spaceBefore=10, spaceAfter=7, keepWithNext=True),
    'caption': ParagraphStyle('caption', fontName='Body', fontSize=9, leading=11.8, spaceAfter=12),
    'cell': ParagraphStyle('cell', fontName='Sans', fontSize=8.5, leading=11),
    'headcell': ParagraphStyle('headcell', fontName='SansB', fontSize=8.5, leading=11),
    'cells': ParagraphStyle('cells', fontName='Sans', fontSize=7.4, leading=9.6),
    'headcells': ParagraphStyle('headcells', fontName='SansB', fontSize=7.4, leading=9.6),
    'ref': ParagraphStyle('ref', fontName='Body', fontSize=9.6, leading=12.5, spaceAfter=5),
}


def inline(s, links=True):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'10\^(-?\d+)', r'10<super>\1</super>', s)
    if links:
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: '<link href="%s" color="#155377">%s</link>' % (m[2], m[1]), s)
    return s


def plain(s):
    return re.sub(r'\*\*(.+?)\*\*', r'\1', s)


source = (P / (NAME + '.md')).read_text(encoding='utf-8')
body_md = source.split('<!-- REFERENCES -->')[0]
lines = body_md.splitlines()
blocks = []      # neutral block list shared by the three writers
i = 0
cols = None
seen_title = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line == '<!-- PAGE -->':
        blocks.append(('page',))
        i += 1
        continue
    m = re.fullmatch(r'<!-- COLS (.+) -->', line)
    if m:
        cols = [float(x) for x in m[1].split()]
        i += 1
        continue
    if line.startswith('# '):
        blocks.append(('title', line[2:]))
        seen_title = 1
        i += 1
        continue
    if line.startswith('## '):
        blocks.append(('h2', line[3:]))
        i += 1
        continue
    if line.startswith('### '):
        blocks.append(('h3', line[4:]))
        i += 1
        continue
    if line.startswith('$$ '):
        num, tex = re.fullmatch(r'\$\$ \((\d+)\) (.+) \$\$', line).groups()
        blocks.append(('eq', int(num), tex))
        i += 1
        continue
    if line.startswith('!['):
        path = P / re.match(r'!\[.*?\]\((.+)\)', line).group(1)
        i += 1
        while not lines[i].strip():
            i += 1
        blocks.append(('fig', path, lines[i].strip()))
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            row = [x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+', c) for c in row):
                rows.append(row)
            i += 1
        blocks.append(('table', rows, cols or [1 / len(rows[0])] * len(rows[0])))
        cols = None
        continue
    buf = [line]
    i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '![', '$$', '<!--')):
        buf.append(lines[i].strip())
        i += 1
    text = ' '.join(buf)
    if seen_title == 1:
        kind, seen_title = 'sub', 2
    elif seen_title == 2:
        kind, seen_title = 'meta', 3
    else:
        kind = 'caption' if re.match(r'Table [A-Z]?\d+\.', text) else 'body'
    blocks.append(('para', text, kind))

# equations as images
eqfile = {}
for b in blocks:
    if b[0] == 'eq':
        fig = plt.figure(figsize=(9, .7))
        fig.patch.set_alpha(0)
        fig.text(.01, .5, '$' + b[2] + '$', fontsize=14, va='center', fontfamily='DejaVu Serif')
        f = P / 'figures' / ('equation_%02d.png' % b[1])
        fig.savefig(f, dpi=320, bbox_inches='tight', pad_inches=.04, transparent=True)
        plt.close(fig)
        eqfile[b[1]] = f

# references: only those cited in the body, in ID order
cited = sorted(set(re.findall(r'R\d\d', re.sub(r'!\[.*?\]\(.*?\)', '', body_md))))
catalog = {r['id']: r for r in json.loads((P / 'reference_catalog.json').read_text(encoding='utf-8'))}
missing = [c for c in cited if c not in catalog]
assert not missing, missing
refs = []
for rid in cited:
    r = catalog[rid]
    url = 'https://doi.org/' + r['doi'] if r.get('doi') else r['url']
    text = '[%s] %s (%s). %s. %s.' % (r['id'], r['authors'], r['year'], r['title'], r['venue'])
    if rid == 'R18':
        text += ' Abstract and metadata reviewed; full text not accessed.'
    refs.append((text, url))
REFNOTE = ('Reference IDs match the project\'s saved reference records. Records that this revision no longer cites are omitted, '
           'so the numbering has gaps.')

# ---------------------------------------------------------------- PDF
story = []
pending_table = -1
for b in blocks:
    k = b[0]
    if k == 'page':
        story.append(PageBreak())
    elif k in ('title', 'h2', 'h3'):
        story.append(Paragraph(inline(b[1]), ST[k]))
    elif k == 'para':
        par = Paragraph(inline(b[1]), ST[b[2]])
        if b[2] == 'caption' and pending_table == len(story):
            # keep a table and its caption on one page
            group = story[-3:] + [par]
            del story[-3:]
            lead = []
            while story and isinstance(story[-1], Paragraph) and story[-1].style.name in ('h2', 'h3'):
                lead.insert(0, story.pop())
            story.append(KeepTogether(lead + group))
        else:
            story.append(par)
    elif k == 'eq':
        iw, ih = PILImage.open(eqfile[b[1]]).size
        fac = min((width - 42) / iw, 72 / 320)
        t = Table([[Image(str(eqfile[b[1]]), width=iw * fac, height=ih * fac), Paragraph('(%d)' % b[1], ST['body'])]],
                  colWidths=[width - 35, 35])
        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                               ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 6),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
        if story and isinstance(story[-1], Paragraph):
            story[-1].keepWithNext = True
        t.keepWithNext = True
        story.append(t)
    elif k == 'fig':
        iw, ih = PILImage.open(b[1]).size
        fac = min(width / iw, 330 / ih)
        img = Image(str(b[1]), width=iw * fac, height=ih * fac)
        img.hAlign = 'CENTER'
        lead = []
        while story and isinstance(story[-1], Paragraph) and story[-1].style.name in ('h2', 'h3'):
            lead.insert(0, story.pop())
        story.append(KeepTogether(lead + [Spacer(1, 5), img, Spacer(1, 7), Paragraph(inline(b[2]), ST['caption'])]))
    elif k == 'table':
        rows, ratios = b[1], b[2]
        small = len(rows[0]) >= 5
        cs, hs = (ST['cells'], ST['headcells']) if small else (ST['cell'], ST['headcell'])
        t = Table([[Paragraph(inline(x), hs if ri == 0 else cs) for x in row] for ri, row in enumerate(rows)],
                  colWidths=[r * width for r in ratios], repeatRows=1, hAlign='LEFT')
        pad = 4 if small else 6
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5eaee')),
                               ('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#d9d9d9')),
                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('LEFTPADDING', (0, 0), (-1, -1), pad), ('RIGHTPADDING', (0, 0), (-1, -1), pad),
                               ('TOPPADDING', (0, 0), (-1, -1), pad), ('BOTTOMPADDING', (0, 0), (-1, -1), pad)]))
        story.extend([Spacer(1, 5), t, Spacer(1, 8)])
        pending_table = len(story)
story.append(PageBreak())
story.append(Paragraph('References', ST['h2']))
story.append(Paragraph(REFNOTE, ST['caption']))
for text, url in refs:
    story.append(Paragraph(inline(text) + ' <link href="%s" color="#155377">%s</link>' % (html.escape(url, quote=True), html.escape(url)), ST['ref']))


def footer(c, doc):
    c.saveState()
    c.setFont('Sans', 8)
    c.setFillColor(colors.HexColor('#333333'))
    c.drawString(50, 28, 'Planet X and SPHEREx project report (revised)')
    c.drawRightString(A4[0] - 50, 28, str(doc.page))
    c.restoreState()


out = P / (NAME + '.pdf')
doc = SimpleDocTemplate(str(out), pagesize=A4, rightMargin=50, leftMargin=50, topMargin=44, bottomMargin=45,
                        title=TITLE, author='Planet X and SPHEREx project', pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)

# ---------------------------------------------------------------- HTML
def h(s):
    return inline(s).replace('<link ', '<a ').replace('</link>', '</a>').replace(' color="#155377"', '')


hb = []
for b in blocks:
    k = b[0]
    if k == 'page':
        hb.append('<hr>')
    elif k == 'title':
        hb.append('<h1>%s</h1>' % h(b[1]))
    elif k in ('h2', 'h3'):
        hb.append('<%s>%s</%s>' % (k, h(b[1]), k))
    elif k == 'para':
        hb.append('<p class="%s">%s</p>' % (b[2], h(b[1])))
    elif k == 'eq':
        hb.append('<div class="equation"><img src="figures/%s" alt="%s"><span>(%d)</span></div>' % (eqfile[b[1]].name, html.escape(b[2], quote=True), b[1]))
    elif k == 'fig':
        hb.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (b[1].relative_to(P).as_posix(), html.escape(plain(b[2]), quote=True), h(b[2])))
    elif k == 'table':
        hb.append('<table>' + ''.join('<tr>' + ''.join(('<th>%s</th>' if j == 0 else '<td>%s</td>') % h(c) for c in row) + '</tr>' for j, row in enumerate(b[1])) + '</table>')
hb.append('<h2>References</h2><p class="caption">%s</p>' % REFNOTE)
for text, url in refs:
    hb.append('<p class="ref">%s <a href="%s">%s</a></p>' % (h(text), url, html.escape(url)))
css = ('body{max-width:900px;margin:45px auto;padding:0 26px;font:18px/1.6 Georgia,serif;color:#161616}h1{font-size:34px;line-height:1.2}'
       'h2,h3{line-height:1.3;margin-top:28px}a{color:#155377}table{border-collapse:collapse;font:14px/1.4 Arial,sans-serif;width:100%;margin:20px 0}'
       'td,th{border:1px solid #d9d9d9;padding:8px;text-align:left;vertical-align:top}th{background:#e5eaee}img{max-width:100%;height:auto}figure{margin:25px 0}'
       'figcaption,.caption{font-size:15px;line-height:1.5}figure img{display:block;max-height:560px;margin:auto}'
       '.equation{display:flex;align-items:center;gap:25px;margin:22px 0}.equation img{max-width:90%;max-height:64px;object-fit:contain}'
       '.ref{font-size:16px;overflow-wrap:anywhere}hr{border:0;margin:40px 0}.meta{font:14px Arial,sans-serif}.sub{font-style:italic}'
       '@media print{body{font-size:11pt}h2,h3{break-after:avoid}figure{break-inside:avoid}}')
(P / (NAME + '.html')).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'
                                  + TITLE + '</title><style>' + css + '</style><body>' + ''.join(hb) + '</body></html>', encoding='utf-8')

# ---------------------------------------------------------------- Word
try:
    import docx
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    d = docx.Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(2)
    d.styles['Normal'].font.name = 'Times New Roman'
    d.styles['Normal'].font.size = Pt(11)

    def runs2(par, s, size=None, italic=False):
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', s)
        for part in re.split(r'(\*\*.+?\*\*)', s):
            if not part:
                continue
            bold = part.startswith('**')
            text = part.strip('*') if bold else part
            for j, seg in enumerate(re.split(r'(?<=10)\^(-?\d+)', text)):
                if seg == '':
                    continue
                r = par.add_run(seg)
                r.font.superscript = (j % 2 == 1)
                r.bold = bold
                r.italic = italic
                if size:
                    r.font.size = Pt(size)
        return par

    for b in blocks:
        k = b[0]
        if k == 'page':
            d.add_page_break()
        elif k == 'title':
            d.add_heading(b[1], 0)
        elif k == 'h2':
            d.add_heading(b[1], 1)
        elif k == 'h3':
            d.add_heading(b[1], 2)
        elif k == 'para':
            p = d.add_paragraph()
            if b[2] == 'caption':
                runs2(p, b[1], 9)
            elif b[2] == 'sub':
                runs2(p, b[1], 12, True)
            elif b[2] == 'meta':
                runs2(p, b[1], 9)
            else:
                runs2(p, b[1])
        elif k == 'eq':
            p = d.add_paragraph()
            iw, ih = PILImage.open(eqfile[b[1]]).size
            p.add_run().add_picture(str(eqfile[b[1]]), width=Cm(min(14, iw / 320 * 2.54 * 0.9)))
            p.add_run('    (%d)' % b[1])
        elif k == 'fig':
            p = d.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            iw, ih = PILImage.open(b[1]).size
            p.add_run().add_picture(str(b[1]), width=Cm(min(16.5, 11.5 * iw / ih)))
            runs2(d.add_paragraph(), b[2], 9)
        elif k == 'table':
            rows, ratios = b[1], b[2]
            t = d.add_table(rows=len(rows), cols=len(rows[0]))
            t.style = 'Table Grid'
            t.autofit = False
            size = 7.5 if len(rows[0]) >= 5 else 8.5
            for ri, row in enumerate(rows):
                for ci, c in enumerate(row):
                    cell = t.cell(ri, ci)
                    cell.width = Cm(17 * ratios[ci])
                    par = cell.paragraphs[0]
                    runs2(par, c, size)
                    if ri == 0:
                        for r in par.runs:
                            r.bold = True
            d.add_paragraph()
    d.add_page_break()
    d.add_heading('References', 1)
    runs2(d.add_paragraph(), REFNOTE, 9)
    for text, url in refs:
        runs2(d.add_paragraph(), text + ' ' + url, 9.5)
    d.core_properties.title = TITLE
    d.core_properties.author = 'Planet X and SPHEREx project'
    d.save(str(P / (NAME + '.docx')))
    print('docx written')
except ImportError:
    print('python-docx not available; Word file skipped')

# keep the Markdown's generated reference list in step with the catalog
(P / (NAME + '.md')).write_text(body_md + '<!-- REFERENCES -->\n\n## References\n\n' + REFNOTE + '\n\n'
                                + '\n\n'.join('%s [%s](%s)' % (t, u, u) for t, u in refs) + '\n', encoding='utf-8')
print(out, out.stat().st_size, 'cited', cited)
