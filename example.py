from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBox, LTChar, LAParams, LTFigure, LTLine, LTAnno
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from PyPDF2 import PdfFileWriter, PdfFileReader
import networkx as nx
import morfeusz2
import datetime
from os.path import isfile, join
from os import listdir
import os


#rzeczy czysto do ekstrakcji
class Pdf:
    def __init__(self, pdf_doc):
        self.pdf_doc = pdf_doc

    def __enter__(self):
        self.fp = open(self.pdf_doc, 'rb')
        parser = PDFParser(self.fp)
        doc = PDFDocument(parser)
        parser.set_document(doc)
        self.doc = doc
        return self

    def _parse_pages(self):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(char_margin=3.5, all_texts=True)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(self.doc):
            interpreter.process_page(page)
            layout = device.get_result()
            yield layout

    def __iter__(self):
        return iter(self._parse_pages())

    def __exit__(self, _type, value, traceback):
        self.fp.close()

class Mp:
    def __init__(self, name, speeches):
        self.name = name
        self.speeches = speeches

class PartyChange:
    def __init__(self, date1, date2, party):
        self.startDate = date1
        self.endDate = date2
        self.party = party

class MyCharacter:
    def __init__(self, text, fontcode, fontname, fontstyle, fontsize):
        self.text = text
        self.fontcode = fontcode
        self.fontname = fontname
        self.fontstyle = fontstyle
        self.fontsize = fontsize

#wyrzuca wszystkie nie-litery z mpsu
def remove_punctuation(mps):

    for mp in mps:
        for char in mp.speeches:
            if not char.isalpha() or char == " ":
                mp.speeches = mp.speeches[:mp.speeches.index(char)] + " " + mp.speeches[mp.speeches.index(char)+1:]
        #mp.speeches = mp.speeches.replace("(", "$#$#$$$")
    return mps

def convertMonth(monthStr):
    months={
        "stycz": 1,
        "lut": 2,
        "mar": 3,
        "kwie": 4,
        "maj": 5,
        "czer": 6,
        "lip": 7,
        "sier": 8,
        "wrze": 9,
        "paź": 10,
        "lis": 11,
        "grud": 12
    }
    for k in months:
        if k in monthStr:
            return months[k]
    print("error: month not reckognized")
    return -1
    

#ekstrakcja tekstu ze strony pdfa do mpsu
def handle_text_box(item, f, mps, actual_name, actualDate):
    for obj in item: #dla kazdej linii
        #jak to zrobic normalnie?
         for c in obj:
            if isinstance(c, LTChar):
                mychar = MyCharacter(c.get_text(), c.fontname[0:6], c.fontname[7:20], c.fontname[21:], c.size) #przeczytanie pierwszego chara zeby zdecydowac czy to imie czy wypowiedz
                actual_speech = ""
                if mychar.fontstyle == "Bold": #to oznacza ze ta linia to imie polityka #mychar.fontcode == "JFUGEF" and
                    actual_name = obj.get_text().strip()[:-1] #wziecie calej linii - imienia i nazwiska polityka i susuniecie dwukropka
                elif mychar.fontstyle == "Normal": #to oznacza ze to przemowa #(mychar.fontcode == "TZUOOL" or mychar.fontcode == "OPHKWV")
                    for c in obj: #czytanie kazdego chara w linii
                        if isinstance(c, LTChar): #costam
                            mychar = MyCharacter(c.get_text(), c.fontname[0:6], c.fontname[7:20], c.fontname[21:], c.size)
                            if mychar.fontstyle == "Normal": #jesli fontstyle to normal to to nie oklaski etc
                                actual_speech = actual_speech + mychar.text #dodanie chara do wypowiedzi
                            # if actual_name == "Wicemarszałek Ryszard Terlecki:":
                            #     print(mychar.text, mychar.fontcode)
                    # print(actual_name)
                    # print(actual_speech)
                    if mychar.fontstyle == "Normal" and "posiedzenie Sejmu w dniu" in actual_speech:
                        date = actual_speech[actual_speech.find("dniu ")+5:]
                        date = date.split(" ")
                        month = convertMonth(date[1])
                        actualDate = datetime.date(int(date[2]), month, int(date[0]))

                    else:
                        if actual_speech[-1] == "-":
                            actual_speech = actual_speech[:-1]

                        mps_len = len(mps)
                        for mp in mps:
                            if mp.name == actual_name:
                                #mp.append_speeches(actual_speech)
                                mp.speeches = mp.speeches + actual_speech
                                #print("dodano wypowiedz: ", actual_speech)
                                #print("i: ", i)
                                break
                            elif mps.index(mp) == mps_len-1:
                                mps.append(Mp(actual_name, actual_speech))
                                #print("dodano polityka: {} i wypowiedz: {}".format(actual_name, actual_speech))
                                #print("i: ", i)
                                break
            break
    return mps, actual_name, actualDate
        # if fontstyle == "Normal" and fontcode == "TZUOOL":
        #     #f.write("{};{};{};{}; size: {} \n".format(text, fontsth, fontname, fontstyle, item.size))
        #     f.write(text)
        #     #print(text)

#usuniecie zbednych stron z pdfa
def deletePages(pdfsIn, pdfsOut, pagesToDelete):
    for pdfIn in pdfsIn:
        pagesToDelete = pagesToDelete # page numbering starts from 0
        infile = PdfFileReader(pdfIn, 'rb')
        output = PdfFileWriter()

        for i in range(infile.getNumPages()):
            if i not in pagesToDelete:
                p = infile.getPage(i)
                output.addPage(p)

        with open(pdfsOut[pdfsIn.index(pdfIn)], 'wb') as f:
            output.write(f)


#sprawdzenie czy dany znacznik reprezentuje slowo ktore sie nadaje tzn. ma jeden z tych fleksemow ktore chcemy zachowac
def checkIfValidPartOfSpeech(markerToCheck, newWord):
    markersTab = ["subst", "depr", "adj", "adja", "adjp", "adjc", "fin", "aglt", "praet", "impt", "imps", "inf", "pcon", "pant", "ger", "pact", "ppas", "xxx"]
    markerToCheck = markerToCheck[:markerToCheck.find(":")]
    newWord = newWord
    for marker in markersTab:
        if marker == markerToCheck or newWord == "prawo":
            return True
    
    return False

#liczenie odległóści edycyjnej wziete od Salvador Dali z https://stackoverflow.com/questions/2460177/edit-distance-in-python
def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

#tworzenie słownika posłów, gdzie key = imię posła a value: lista jego zmian przynależności
def makeMpChanges():
    mpsFile = open("poslowie.txt", "r")
    clubs = mpsFile.read().split('$')
    mpsFile.close()

    mpsDict = {}

    #dodanie do słownika wszystkich posłów, którzy dostali się do sejmu od razu i wrzucenie im defaultowo dat od początku do końca
    for club in clubs:
        tmp = club.split(":")
        accClub = tmp[0]
        accMpsS = tmp[1]
        accMpsList = accMpsS.split(",")
        accDate = datetime.date(2015,11,11)
        for accMp in accMpsList:
            accMp = accMp[1:accMp.find("(")-1]
            accMp = accMp[:accMp.find(" ")+2] + accMp[accMp.find(" ")+2:].lower()
            if "-" in accMp:
                accMp = accMp[:accMp.find("-")+1] + accMp[accMp.find("-")+1].upper() + accMp[accMp.find("-")+2:]
            newPartyChange = PartyChange(accDate, datetime.date(2019,1,1), accClub)
            mpsDict[accMp] = [newPartyChange]


    membFile = open("przynaleznosc.txt", "r", encoding='utf-8-sig')
    byDateList = membFile.read().split('$')
    mpsFile.close()

    #dodanie do słownika posłów, którzy dostali się do sejmu później lub dodanie zmian do listy zmian przynależności
    for byDate in byDateList:
        tmp = byDate.split(":")
        accDate = tmp[0]
        accDate = accDate.split(".")
        accDate = datetime.date(int(accDate[2]), int(accDate[1]), int(accDate[0]))
        tmp = tmp[1].split("+")
        accMp = tmp[0][1:]
        accClub = tmp[1][:-1]
        if accMp in mpsDict:
            mpsDict[accMp][-1].endDate = accDate - datetime.timedelta(days=1)
            mpsDict[accMp] = mpsDict[accMp] + [PartyChange(accDate, datetime.date(2019,1,1), accClub)]
        else:
            newPartyChange = PartyChange(accDate, datetime.date(2019,1,1), accClub)
            mpsDict[accMp] = [newPartyChange]

    return mpsDict

def mergeInvalidMps(mps):
    mpToDelete = []
    for mp1 in mps:
        for mp2 in mps:
            distance = levenshteinDistance(mp1.name, mp2.name) #analiza dystansu
            if distance < 2 and mps.index(mp1) != mps.index(mp2): 
                if len(mp1.name) > len(mp2.name):
                    mp1.speeches = mp1.speeches + mp2.speeches #mergowanie wypowiedzi
                    mpToDelete += [mps.index(mp2)]
                else:
                    mp2.speeches = mp2.speeches + mp1.speeches #mergowanie wypowiedzi
                    mpToDelete += [mps.index(mp1)]
    mpToDelete = list(set(mpToDelete)) #usunięcie duplikatów na liście

    #usunięcie zbędnych mp czyli takich, którzy się powtarzają
    for i in sorted(mpToDelete, reverse=True):
        del mps[i]
    return mps
def morfAnalyseAndCorrect(mps):
    morf = morfeusz2.Morfeusz(praet='composite')
    mpToDelete = []
    for mp in mps:
        #print("analysing speeches of: ", mp.name)
        newSpeeches = []
        for text in mp.speeches:
            analysis = morf.analyse(text)
            noOfInterpretation = 0
            for interpretation in analysis:
                newWord = interpretation[2][1]
                if interpretation[0] ==  noOfInterpretation: #jesli jeszcze tego slowa nie analizowalismy i jeszcze nie wystepuje  and (newWord not in newSpeeches) 
                    if checkIfValidPartOfSpeech(interpretation[2][2], newWord): #jeśli slowo jest wazna czescia mowy - usuwamy "i", "tam", "gdzie" etc
                        newSpeeches.append(newWord)
                        noOfInterpretation += 1
        mp.speeches = newSpeeches
        
        #wyrzucenie wszystkiego co stoi przed imieniem typu "Poseł" czy "Wicemarszałek", i jeśli nic nie zostanie, bo nie ma imienia to potem będzie można usunąć danego mp
        namelist = mp.name.split(" ")
        wordsToDelete = []
        for name in namelist:
            analysis = morf.analyse(name)
            isName = False 
            for interpretation in analysis:
                if interpretation[2][3] == ["imię"]: #jeśli morfeuszowi wyszło że to imię
                    isName = True
                    break #to przerywamy dalsze interpretacje, żeby zaoszczędzić obliczeń
            if (not isName): # jeśli dane słowo nie jest imieniem to dodajemy je do listy słów do usunięcia # <<and name != "Marszałek">> ale chyba nie bo marszałek i tak nic ciekawego nie mówi  
                wordsToDelete += [namelist.index(name)]
            else: # a jeśli jest imieniem to przerywamy, reszta wchodzi
                break

        #usunięcie słów do pierwszego słowa, które jest imieniem
        for i in sorted(wordsToDelete, reverse=True):
            del namelist[i]
        
        #jeśli name stało się puste, bo nie zawierało żadnego słowa, które jest imieniem to aktualne mp jest dodawane do listy do usunięcia
        if not namelist: #jeśli pusta
            mpToDelete += [mps.index(mp)]

        #aktualizacja mp.name tak, żeby nie zawierało nic przed imieniem
        newName = ""
        for item in namelist:
            newName += item + " "
        mp.name = newName[:-1]

    #usunięcie mp, które miały puste name (czyli te, które nie zawierały słów, które są imionami)
    for i in sorted(mpToDelete, reverse=True):
        del mps[i]
    return mps

def makeListsFromStrings(mps):
    for mp in mps:
        newSpeeches = []
        mp.speeches = mp.speeches + " "
        while mp.speeches.find(" ") != -1: #przerzucanie słów z speeches do newSpeeches tak długo aż będą jeszcze jakieś spacje 
            newWord = mp.speeches[:mp.speeches.find(" ")]
            if newWord != '':
                newSpeeches.append(newWord)
            mp.speeches = mp.speeches[mp.speeches.find(" ")+1:]
        mp.speeches = newSpeeches
        if len(mps) < 2: #szybkie wyrzucenie jakiś śmieci - żaden polityk nie będzie miał w przmówieniu jednego słowa
            mps = mps[:mps.index(mp)] + mp.speeches[mps.index(mp)+1:]
    return mps

#dodanie aktualnej przynależności do imion posłów np "Jarosław Kaczyński" -> "Jarosław Kaczyński PiS"
def appendNamesWithParty(mps, mpChanges, actualDate):
    mpsToDelete = []

    for mp in mps:
        foundOne = True
        if mp.name not in mpChanges: #jeśli się taki poseł nie znalazł w słowniku to może oznaczać, że to wcale nie poseł tylko wdarł się na mównicę, albo jest jakiś inny błąd
            foundOne = False
            for k in mpChanges:
                if levenshteinDistance(mp.name, k) < 2: #taki błąd to na przykład to, że brakuje ostatniej litery nazwiska
                    mp.name = k #to wtedy naprawiamy
                    foundOne = True
                    break
            if not foundOne: #ale jeśli to imię nie pasuje do żadnych w słowniku to usuwamy
                mpsToDelete.append(mps.index(mp)) #tu niestety są usuwani też posłowie typu Roman Kosecki != Roman Jacek Kosecki
                #TODO: ew zrobić tak, żeby to jakoś rozpoznawało że brakuje imienia w środku
                print("Warning: {} appears not to be a member of parliament".format(mp.name))
        if foundOne:
            listOfMpPartyChanges = mpChanges[mp.name]
            for pChange in listOfMpPartyChanges:
                if actualDate > pChange.startDate and actualDate < pChange.endDate:
                    mp.name = mp.name + " " + pChange.party
                    break
    for i in sorted(mpsToDelete, reverse=True):
        del mps[i]    
    return mps

def mergeMps(curMps, mps):
    merged = 0
    appended = 0
    for curMp in curMps:
        foundMp = False
        for mp in mps:
            if curMp.name == mp.name:
                mp.speeches += curMp.speeches
                foundMp = True
                merged +=1
                break
        if not foundMp:
            mps.append(curMp)
            appended+=1
    return mps


#########################################################################################################################    

if __name__ == "__main__":
    
    mpChanges = makeMpChanges()
    os.chdir(r'C:\Users\MarcinM\Documents\studia\TASS\2\stenogramy\przetworzone2')


    # odkomentowa/ zakomentować żeby wpuścić pełną werję stenogramu
    #usuwanie niepotrzebnych stron
    path = r'C:\Users\MarcinM\Documents\studia\TASS\2\stenogramy\przetworzone2'
    pdfs = [f for f in listdir(path) if isfile(join(path, f))]
    #pdfsOut = ["stenshort.pdf"]
    
    mps = []

    #extrakcja danych
    for pdf in pdfs:
        with Pdf(pdf) as doc:
            print("Processing pdf: ", doc.pdf_doc)
            f=open("data.txt", "w+", encoding='utf8')

            curMps = []
            actual_name = "unidentified"
            curMps.append(Mp("unidentified", ""))
            actualDate1 = (1,1,1)
            #właściwa ekstrakcja
            for page in doc:
                if page.pageid % 10 == 0:
                    print("Extracting data from page: {}...".format(page.pageid))

                for item in page:
                    if isinstance(item, LTTextBox):
                        curMps, actual_name, actualDate = handle_text_box(item, f, curMps, actual_name, actualDate1)
                    if actualDate != actualDate1:
                        actualDate1 = actualDate

            #wyrzucenie wszystkich nie-liter
            curMps = remove_punctuation(curMps)

            #przerobienie długich stringów (całych wypowiedzi) na listę słów
            curMps = makeListsFromStrings(curMps)           

            #analiza morfologiczna, wyrzucenie tytułów i wyrzucenie namesów które są błędne (nie-imiona)
            curMps = morfAnalyseAndCorrect(curMps)
            
            #analiza odleglosci Levensteina żeby zmergować wypowiedzi tego samego posła, jeśli wystąpiły błędy w czytaniu jego imienia typu "Joanna Lichock" i "Joanna Lichocka"
            curMps = mergeInvalidMps(curMps)
            
            #actualDate = datetime.date(2018,11,21) 
            curMps = appendNamesWithParty(curMps, mpChanges, actualDate)

            mps = mergeMps(curMps, mps)
    
    
    os.chdir(r'C:\Users\MarcinM\Documents\studia\TASS\2')
    #wyrzucenie mps do pliku txt
    # for mp in mps:
    #     f.write("\n")
    #     f.write("\n")
    #     f.write(mp.name)
    #     f.write("\n")
    #     for word in mp.speeches:
    #         f.write(word + " ")
    # f.close()

    #stworzenie grafu
    G = nx.Graph()
    for mp in mps:
        G.add_node(mp.name, bipartite=0)

        for word in mp.speeches:
            G.add_node(word, bipartite=1)
            if not G.has_edge(mp.name, word):
                G.add_edge(mp.name, word, weight = 1)
            else:
                G[mp.name][word]['weight'] += 1
    # print(nx.number_of_edges(G))
    # print(nx.number_of_nodes(G))
    # print(G['Ryszard Terlecki PiS'])
    nx.write_graphml(G, "testgraphml.graphml")
    nx.write_gml(G, "testgml.gml")

    #TODO: zmiana dat dla każdego pdfa - wykrywanie z pdf? ręcznie?
    #TODO: automatyczne wykrywanie początku wypowiedzi?
    

    #TODO: analiza już



