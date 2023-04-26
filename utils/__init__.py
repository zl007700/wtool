
def doc2docx(fpin, fpout):
    """ doc文件转docx文件 """
    from win32com import client as wc 
    from pathlib import Path
    f_path = Path(fpin.resolve())
    wps = wc.gencache.EnsureDispatch('kwps.application')
    doc = wps.Documents.Open(str(f_path))
    doc.SaveAs(fpout, 12)
    doc.Close()
    wps.Quit()


def docx2txt(fpin, fpout):
    """ docx文件转txt文件  """
    from docx import Document
    from pathlib import Path
    from zipfile import ZipFile
    from bs4 import BeautifulSoup

    f_path = Path(fpin)
    try:
        doc = Document(str(f_path))
        paragraphs = [param.text for param in doc.paragraphs]
    except:
        try:
            document = ZipFile(str(f_path))
            xml = document.read('word/document.xml')
            word = BeautifulSoup(xml.decode('utf-8'))
            paragraphs = [item.text for item in word.findAll('w:t')]
        except:
            return
    with open(fpout, 'w', encoding='utf-8') as fout:
        fout.write("\n".join(paragraphs))


def loadFile(f, encoding='utf-8'):
    with open(f, 'r', encoding=encoding) as fin:
        for lineid, line in enumerate(fin):
            yield lineid, line.strip()


def loadJsonFile(f, encoding='utf-8', gen=False):
    import json
    datas =  []
    for lineid, line in loadFile(f, encoding=encoding):
        d = json.loads(line)
        datas.append((lineid, d))
    return datas


def loadJsonFileGen(f, encoding='utf-8', gen=False):
    import json
    for lineid, line in loadFile(f, encoding=encoding):
        d = json.loads(line)
        yield lineid, d

