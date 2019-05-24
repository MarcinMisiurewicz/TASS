from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from io import StringIO
import io
import os

def convert_pdf_to_txt(path, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)
    device = PDFPageAggregator(manager, laparams=LAParams())

    infile = open(path, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
        layout = device.get_result()
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    return text

text = convert_pdf_to_txt('sten.pdf', pages=[40,41,42])
text_file = open("data.txt", "w", encoding="utf-8")
text_file.write(text)
text_file.close()
