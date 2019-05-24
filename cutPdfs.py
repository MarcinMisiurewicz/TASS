from PyPDF2 import PdfFileWriter, PdfFileReader
from os import listdir
from os.path import isfile, join
import os


def deletePages(pdfIn, pagesToDelete):
    os.chdir(r'C:\Users\MarcinM\Documents\studia\TASS\2\stenogramy\nieprzetworzone')
    pagesToDelete = pagesToDelete # page numbering starts from 0
    infile = PdfFileReader(pdfIn, 'rb')
    output = PdfFileWriter()
    
    pdfOut = pdfIn[:-4] + "_cut.pdf"

    for i in range(infile.getNumPages()):
        if i not in pagesToDelete:
            p = infile.getPage(i)
            output.addPage(p)
    os.chdir(r'C:\Users\MarcinM\Documents\studia\TASS\2\stenogramy\przetworzone')
    with open(pdfOut, 'wb') as f:
        output.write(f)



path = r'C:\Users\MarcinM\Documents\studia\TASS\2\stenogramy\nieprzetworzone'
pdfs = [f for f in listdir(path) if isfile(join(path, f))]

for pdf in pdfs:
    deletePages(pdf, list(range(0, 9)))
