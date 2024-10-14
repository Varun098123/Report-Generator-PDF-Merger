from flask import Flask, request, send_file, render_template
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    sections = {}
    cover_page_file = request.files.get('cover_page_pdf')

    # Create a PdfWriter object
    writer = PdfWriter()

    if cover_page_file:
        # Add the cover page
        cover_page_reader = PdfReader(cover_page_file)
        writer.add_page(cover_page_reader.pages[0])

    # Process the sections
    for key, file in request.files.items():
        if key.startswith('pdf_files_'):
            section_num = key.split('_')[2]
            if section_num not in sections:
                sections[section_num] = []
            sections[section_num].append(file)

    for section_num, files in sorted(sections.items(), key=lambda x: int(x[0])):
        section_title = request.form[f'section_title_{section_num}']
        font_style = request.form.get(
            f'font_style_{section_num}', 'Helvetica-Bold')
        font_size = int(request.form.get(f'font_size_{section_num}', '24'))
        font_color = request.form.get(f'font_color_{section_num}', '#000000')
        alignment = request.form.get(f'alignment_{section_num}', 'center')

        first_page = True
        for file in files:
            reader = PdfReader(file)
            for i, page in enumerate(reader.pages):
                if first_page:
                    page = overlay_title_on_page(
                        page, section_title, font_style, font_size, font_color, alignment)
                    first_page = False  # Ensure the title is only applied to the first page
                writer.add_page(page)

    output_stream = BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)

    return send_file(output_stream, as_attachment=True, download_name='merged_pdfs.pdf')

def overlay_title_on_page(page, title, font_style, font_size, font_color, alignment):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Title formatting
    can.setFont(font_style, font_size)  # Use the selected font style and size
    text_width = can.stringWidth(title, font_style, font_size)
    title_x = (letter[0] - text_width) / \
        2 if alignment == 'center' else 20 if alignment == 'left' else letter[
            0] - text_width - 20
    title_y = letter[1] - 40

    can.setFillColor(font_color)
    # Align title based on user selection
    can.drawString(title_x, title_y, title)
    can.save()

    packet.seek(0)
    new_pdf = PdfReader(packet)
    overlay = new_pdf.pages[0]

    # Overlay the title on the existing page
    page.merge_page(overlay)
    return page

if __name__ == '__main__':
    app.run(debug=True)
