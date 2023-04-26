#coding=utf-8
import os
import time
import math
import logging
import collections
import finalseg as finalseg
from data_utils import DataUtils


logger = logging.getLogger("Segger")

class Seg(object):

    def __init__(self):

        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self.dict_dir_path = os.path.join(self.dir_path, 'word_dict')
        self.du = DataUtils()

        fs = os.listdir(self.dict_dir_path)
        for f in fs:
            if f.startswith('seg.dict'):
                dict_path = os.path.join(self.dict_dir_path, f)
                break

        ## Word Dict
        print('Load Word Dict')
        st = time.time()
        self.word_dict = self.loadWordDict(dict_path)
        print('Time used ', time.time() - st)

        ## Stop Dict
        print('Load Stop Dict')
        stop_dict_p = os.path.join(self.dict_dir_path, 'stop.dict.0')
        self.stop_dict = self.loadDict(stop_dict_p)
        print('Dict Load OK')

        self.init()

    def init(self):
        ## Initialization
        text = '《乘风破浪的姐姐》是芒果TV推出的女团成长综艺节目，由黄晓明担任女团发起人。'
        self.lcut(text)
        self.keywords(text, 10)

    def loadWordDict(self, dict_path):
        ##
        ##  Word: [wc, wc_wangmei, wc_weibo, wc_luntan, wc_pinglun]  
        ##

        dict_out = {}
        with open(dict_path, 'r', encoding='utf-8') as fo:
            for line in fo:
                info = line.strip().split('\t')
                w = info[0]
                if w not in dict_out:
                    dict_out[w] =  info[1:]
                else:
                    if dict_out[w][0] == 0:
                        dict_out[w] =  info[1:]

                if w in ['[GLOBAL_WORD_COUNT]', '[GLOBAL_DOC_COUNT]']:
                    continue

                for ch in range(len(w)):
                    wfrag = w[:ch + 1]
                    if wfrag not in dict_out:
                        dict_out[wfrag] = [0,0,0,0,0,'x']
        return dict_out

    def loadDict(self, dict_path):
        dict_out = set()
        with open(dict_path, 'r', encoding='utf-8') as fo:
            for w in fo:
                if w.strip():
                    dict_out.add(w.strip())
        return dict_out

    def getWordCount(self, word, cat='all'):
        if cat == 'all':
            ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[0]
        elif cat == 'wangmei':
            ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[1]
        elif cat == 'weibo':
            ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[2]
        elif cat == 'luntan':
            ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[3]
        elif cat == 'pinglun':
            ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[4]
        else:
            ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[0]
        return int(ret)

    def getIDF(self, word, cat='all'):
        wc = self.getWordCount(word, cat)
        dc = self.getWordCount('[GLOBAL_DOC_COUNT]', cat)

        if wc <= 1:
            wc = 1
            idf = math.log( dc / wc ) / 2
        else:
            idf = math.log( dc / wc )
        return idf

    def getPos(self, word, cat='All'):
        ret = self.word_dict.get(word, [0,0,0,0,0,'x'])[5]
        return ret

    def getDAG(self, sentence):
        DAG = {}
        N = len(sentence)
        for k in range(N):
            tmplist = []
            i = k
            frag = sentence[k]
            while i < N and frag in self.word_dict:
                if len(frag)==1 or self.getWordCount(frag)>0:
                    tmplist.append(i)
                i += 1
                frag = sentence[k:i + 1]
            if not tmplist:
                tmplist.append(k)
            DAG[k] = tmplist
        return DAG

    def calcRoute(self, sentence, DAG, route):
        N = len(sentence)
        route[N] = (0, 0)
        logtotal = math.log(self.getWordCount('[GLOBAL_WORD_COUNT]'))
        for idx in range(N - 1, -1, -1):
            route[idx] = max((math.log(self.getWordCount(sentence[idx:x + 1]) or 1) -
                              logtotal + route[x + 1][0], x) for x in DAG[idx])
        return route

    def cutDAG(self, sentence):
        DAG = self.getDAG(sentence)
        route = {}
        self.calcRoute(sentence, DAG, route)
        x = 0
        buf = ''
        N = len(sentence)
        while x < N:
            y = route[x][1] + 1
            l_word = sentence[x:y]
            if y - x == 1:
                buf += l_word
            else:
                if buf:
                    if len(buf) == 1:
                        yield buf
                        buf = ''
                    else:
                        if not self.word_dict.get(buf):
                            recognized = finalseg.cut(buf)
                            for t in recognized:
                                yield t
                        else:
                            for elem in buf:
                                yield elem
                        buf = ''
                yield l_word
            x = y
        if buf:
            if len(buf) == 1:
                yield buf
            elif not self.word_dict.get(buf):
                recognized = finalseg.cut(buf)
                for t in recognized:
                    yield t
            else:
                for elem in buf:
                    yield elem

    def lcut(self, sent, need_clean=False, need_pos=False):
        sent = self.du.deLuanma(sent)
        sent = self.du.deUtf8(sent)

        if need_clean:
            sent = self.du.deWeiboEmotion(sent)
            sent = self.du.deHandles(sent)

        sent, rep_dict = self.du.preReplace(sent)
        ws = [w.strip() for w in self.cutDAG(sent) if w.strip()]

        if need_pos:
            poses = [self.getPos(w) for w in ws]
            ws, poses = self.du.postReplace(ws, rep_dict, poses)
            return ws, poses
        else:
            ws = self.du.postReplace(ws, rep_dict)
            return ws

    def keywords(self, words, topK=10, poses=None, pos_remain='all', doc_type='all'):
        if isinstance(words, str):
            words = self.lcut(words)

        ## Pos strategy
        pos_group_mode = {}
        pos_group_mode['all'] = ('a', 'ad', 'an', 'g', 'i', 'j', 'l', 'm', 'n', 'nr', 'ns', \
                                  'nt', 'nz', 'q', 's', 'tg', 't', 'v', 'vd', 'vn', 'x', 'z', 'eng', 'PRODUCT', 'DQUOTE', 'DECIMAL', 'URL','IP', 'PHONE', 'NUMBER')

        pos_group_mode['recommend'] = ('g', 'i', 'j', 'l', 'n', 'nr', 'ns', \
                              'nt', 'nz', 'tg', 't', 'v', 'vd', 'vn', 'eng', 'PRODUCT', 'DQUOTE','DECIMAL')

        pos_group_mode['simple'] = ('g', 'i', 'j', 'l', 'n', 'nr', 'ns', \
                              'nt', 'nz', 'vd', 'vn', 'eng')

        if poses and len(poses)==len(words):
            words = [w for w_id,w in enumerate(words) if poses[w_id] in pos_group_mode[pos_remain]]
        else:
            words = [w for w in words if self.getPos(w) in pos_group_mode[pos_remain]]

        words = [w for w in words if w not in self.stop_dict]
        words = self.du.deBlackWords(words)
        words = self.du.deCheckWords(words)
        words = self.du.deNotWords(words)
        words = self.du.deShortWords(words)
        words = self.du.deDigit(words)
        words = self.du.deSymbolWord(words)

        tc = collections.Counter(words)

        tfidf = [ (w, self.getIDF(w, doc_type) * math.log(tc.get(w,1)+1) ) for w in tc.keys()]

        tfidf_order = sorted(tfidf, key=lambda kv:kv[1], reverse=True)

        ret_key = [item[0] for item in tfidf_order[:topK]]
        return ret_key

if __name__ == "__main__":
    text = "中强震@许闯Trunk | 2018摄影封面集#coverfx封面[超话]# 许闯今年不仅为老朋友倪妮/李宇春/angelababy/姚晨拍摄封面，何穗少林禅宗/袁泉/周韵/俞飞鸿/李嫣首封/摄影师陈漫均让人惊喜，还有贝克汉姆/段亦宏/黄渤/陈坤/邓伦/井柏然/邪不压正三人组/蔡徐坤/易烊千玺 等各路男神～ "
    sg = Seg()
    #while True:
        #text = input()
    ws = sg.lcut(text)
    print(ws)
    print(sg.keywords(ws))

