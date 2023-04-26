
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


def trainTestSplit(datas, por=0.2, test_size=None):
    if test_size and test_size > 0:
        train, dev = datas[:-test_size], datas[-test_size:]
        return train, dev
    train_size = int(len(datas) * 0.8)
    train, dev = datas[:train_size], datas[train_size:]
    return train, dev
    
    
def save_train_datas(output_dir, train, dev):
    import json
    from pathlib import Path
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True)
    with open(str(Path(output_dir) / 'train.txt'), 'w', encoding='utf-8') as fout:
        for d in train:
            if isinstance(d, dict):
                d = json.dumps(d, ensure_ascii=False)
            fout.write("%s\n" % str(d))
    with open(str(Path(output_dir) / 'dev.txt'), 'w', encoding='utf-8') as fout:
        for d in dev:
            if isinstance(d, dict):
                d = json.dumps(d, ensure_ascii=False)
            fout.write("%s\n" % str(d))