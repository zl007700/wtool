#coding=utf-8
import os
import re

dict_dir = os.path.abspath(os.path.dirname(__file__))
dict_dir = os.path.join(dict_dir, 'word_dict')
stop_dict_path = os.path.join(dict_dir, 'stop_dict.txt')
blacklist_path = os.path.join(dict_dir, 'blacklist.txt')
checklist_path = os.path.join(dict_dir, 'checklist.txt')
notlist_path = os.path.join(dict_dir, 'notDict.txt')
weibo_emotion_path = os.path.join(dict_dir, 'weibo_emotion.txt')
pos_path = os.path.join(dict_dir, 'pos.txt')
neg_path = os.path.join(dict_dir, 'neg.txt')

class DataUtils():

    _posword_dict = None
    _negword_dict = None
    _stopword_word = None
    _blackword_dict = None
    _sensitiveword_dict = None
    _notword_dict = None
    _langid = None

    def __init__(self):
        self.stop_dict = set()
        self.blacklist = set()
        self.checklist = set()
        self.weibo_emotion_list = set()
        self.poslist = set()
        self.negilst = set()
        self.notlist = set()

    def loadDict(self, dict_name, dict_path):
        with open(dict_path, 'r', encoding='utf-8') as fo:
            for w in fo:
                if w.strip():
                    dict_name.add(w.strip())

    def extractPosNegWord(self, words):
        if not self.poslist:
            self.loadDict(self.poslist, dict_dir + "/pos.txt")
        if not self.negilst:
            self.loadDict(self.negilst, dict_dir + "/neg.txt")

        pos = []
        neg = []
        for w in words:
            if w in self.poslist:
                pos.append(w)
            if w in self.negilst:
                neg.append(w)
        return pos,neg

    def preReplace(self, text):
        def IncReplace(text, reg, tag):
            ret_text = ""
            ret_dict = {}
            last_ed  = 0
            ret = re.finditer(reg, text)
            for v_id, v in enumerate(ret):
                st,ed = v.span()
                if tag in ['PRODUCT', 'DQUOTE']:
                    st += 1
                    ed -= 1
                tag_key = "[_%s_%d_]" %(tag, v_id)
                ret_text = ret_text + text[last_ed:st] + tag_key
                last_ed = ed
                if tag in ['PRODUCT', 'DQUOTE']:
                    ret_dict[tag_key] = v.group(1)
                else:
                    ret_dict[tag_key] = v.group(0)
                if v_id >= 100:
                    break
            ret_text = ret_text + text[last_ed:]
            return ret_text, ret_dict
        
        ret_text = text
        ret_info_dict = {}

        ## 书名等PRODUCT
        reg_exp = r"《(.{,15}?)》"
        ret_text, ret_info_dict['PRODUCT'] = IncReplace(ret_text, reg_exp, 'PRODUCT')
        
        ## 双引DQUOTE
        reg_exp = r"“(.{,15}?)”"
        ret_text, ret_info_dict['DQUOTE'] = IncReplace(ret_text, reg_exp, 'DQUOTE')
        
        ## URL
        reg_exp = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        ret_text, ret_info_dict['URL'] = IncReplace(ret_text, reg_exp, 'URL')
        
        ## DOMAIN
        tails = ['com','cn','org','co','jp','uk','us']
        domain_in = False
        for tail in tails:
            if tail in ret_text:
                domain_in = True
                break
        if domain_in:
            reg_exp = r"(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F])){,15}\.[com|cn|org|co|jp|uk|us]+"
            ret_text, ret_info_dict['DOMAIN'] = IncReplace(ret_text, reg_exp, 'DOMAIN')
        else:
            ret_text, ret_info_dict['DOMAIN'] = ret_text, {}
        
        ## IP
        reg_exp = r"\d+\.\d+\.\d+\.\d+"
        ret_text, ret_info_dict['IP'] = IncReplace(ret_text, reg_exp, 'IP')

        ## PHONE
        reg_exp = r"\d{3}-\d{8}|\d{4}-\d{7}|\d{3}-\d{7}"
        ret_text, ret_info_dict['PHONE'] = IncReplace(ret_text, reg_exp, 'PHONE')
        
        ## DECIMAL
        reg_exp = r"(\-|\+)?\d+\.(\d+)?"
        ret_text, ret_info_dict['DECIMAL'] = IncReplace(ret_text, reg_exp, 'DECIMAL')
        
        ## NUMBER
        reg_exp = r"\d{5,}"
        ret_text, ret_info_dict['NUMBER'] = IncReplace(ret_text, reg_exp, 'NUMBER')

        return ret_text, ret_info_dict


    def postReplace(self, ws, rep_dict, poses=None):
        rep_dict_word = {}
        for rep_type, rep_d in rep_dict.items():
            for k,v in rep_d.items():
                rep_dict_word[k] = v

        nws  = []
        npos = []
        for w_id, w in enumerate(ws):
            if w in rep_dict_word:
                nws.append(rep_dict_word[w])

                if poses:
                    pos_info = w.split('_')
                    if len(pos_info) == 4:
                        npos.append(pos_info[1])
                    else:
                        npos.append('x')

            else:
                nws.append(w)

                if poses:
                    npos.append(poses[w_id])

        if poses:
            return nws, npos
        else:
            return nws


    def deWeiboHeader(self, text):
        # 过滤内容
        filter_list = [ \
            "转发微博",\
            "提示信息",\
            "分享图片",\
            "轉發微博",\
            "分享圖片",\
            "分享单曲",\
            "分享單曲",\
        ]

        for filter_item in filter_list:
            if filter_item in text[:5]:
                text = text[5:]
                break
        return text

    def deUrl(self, text):
        regex = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            )
        urls = re.findall(regex, text)
        for u in urls:
            text = text.replace(u, '')
        return text

    def deSymbol(self, text):
        regex = re.compile(
            r"[\.\!\/_,$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）]+"
            )
        simbols = re.findall(regex, text)
        for s in simbols:
            text = text.replace(s, ' ')

        text = text.replace('\n','')
        text = text.replace('\r','')
        text = text.replace('\u200b','')
        return text.strip()

    def deUtf8(self, text):
        #目前可以去掉表情
        regex = re.compile(
            u'[\U00010000-\U0010ffff]'
            )
        emos = re.findall(regex, text)
        for e in emos:
            text = text.replace(e, '')
        return text

    def deWeiboEmotion(self, text):
        if not self.weibo_emotion_list:
            self.loadDict(self.weibo_emotion_list, weibo_emotion_path)

        for w in self.weibo_emotion_list:
            text = text.replace(w, "")
        return text

    def deStopWords(self, words):
        if not self.stop_dict:
            self.loadDict(self.stop_dict, stop_dict_path)

        w_filterd = []
        for w in words:
            if w in self.stop_dict:
                continue
            w_filterd.append(w)
        return w_filterd

    def deBlackWords(self, words):
        if not self.blacklist:
            self.loadDict(self.blacklist, blacklist_path)

        w_filterd = []
        for w in words:
            if w in self.blacklist:
                continue
            w_filterd.append(w)
        return w_filterd

    def deCheckWords(self, words):
        if not self.checklist:
            self.loadDict(self.checklist, checklist_path)

        w_filterd = []
        for w in words:
            if w in self.checklist:
                continue
            w_filterd.append(w)
        return w_filterd

    def deNotWords(self, words):
        if not self.notlist:
            self.loadDict(self.notlist, notlist_path)

        w_filterd = []
        for w in words:
            if w in self.notlist:
                continue
            w_filterd.append(w)
        return w_filterd

    def deHandles(self, text):
        # Handels(用户ID的过滤；微博、Twitter中很多明星的ID是实名的，后期可以考虑利用)
        # 此处用的python中的re，w匹配范围扩展到了Unicode编码段（字母、数字、下划线），单独的汉字也能匹配
        hndl_regex = re.compile(r"@(\w+)\s")
        return re.sub(hndl_regex, ' ', text)

    def deLuanma(self, text):
        # 去除\x01这类乱码数据
        text = text.replace("\x01","").replace("\x02","").replace("\x03","").replace("\x04","").replace("\x05","").replace("\x06","").replace("\x07","").replace("\x08","").replace("\x09","")
        return text

    def deShortWords(self, words):
        # 过滤过短关键词
        new_tag = []
        for t in words:
            t = t.strip()
            if len(t) < 2:
                continue
            new_tag.append(t)
        return new_tag

    def deDigit(self, words):
        # 过滤纯数字
        new_tag = []
        for t in words:
            if t.isdigit():
                continue
            new_tag.append(t)
        return new_tag

    def deSymbolWord(self, words):
        ret_words = []
        for w in words:
            try:
                checked_w = re.search(r"[\u4e00-\u9fa5a-zA-Z0-9]+", w).group(0)
                if checked_w == w:
                    ret_words.append(w)
            except:
                pass
        return ret_words

    def _creatDict(self, argv = None):
        """
        构建字典
        存储正向情感词、负向情感词、停止词、黑名单词、敏感词（主要为政治敏感词）
        :return:返回字典
        """
        if argv == 'is_pos':
            # 正向词典文件存储为字典
            dict_words = {}
            with open(pos_path, 'r', encoding='utf-8') as f_pos:
                lines = f_pos.readlines()
                for line in lines:
                    line = line.rstrip('\n')
                    if line in dict_words:
                        continue
                    else:
                        dict_words[line] = True
            self._posword_dict = dict_words
        elif argv == 'is_neg':
            # 负向词典文件存储为字典
            dict_words = {}
            with open(neg_path, 'r', encoding='utf-8') as f_neg:
                lines = f_neg.readlines()
                for line in lines:
                    line = line.rstrip('\n')
                    if line in dict_words:
                        continue
                    else:
                        dict_words[line] = True
            self._negword_dict = dict_words
        elif argv == 'is_stopword':
            # 停止词典文件存储为字典
            dict_words = {}
            with open(stop_dict_path, 'r', encoding='utf-8') as f_stop:
                lines = f_stop.readlines()
                for line in lines:
                    line = line.rstrip('\n')
                    if line in dict_words:
                        continue
                    else:
                        dict_words[line] = True
            self._stopword_word = dict_words
        elif argv == 'is_blackword':
            # 黑名单词典文件存储为字典
            dict_words = {}
            with open(blacklist_path, 'r', encoding='utf-8') as f_black:
                lines = f_black.readlines()
                for line in lines:
                    line = line.rstrip('\n')
                    if line in dict_words:
                        continue
                    else:
                        dict_words[line] = True
            self._blackword_dict = dict_words
        elif argv == 'is_sensitiveword':
            # 敏感词典文件存储为字典
            dict_words = {}
            with open(checklist_path, 'r', encoding='utf-8') as f_sensitive:
                lines = f_sensitive.readlines()
                for line in lines:
                    line = line.rstrip('\n')
                    if line in dict_words:
                        continue
                    else:
                        dict_words[line] = True
            self._sensitiveword_dict = dict_words
        elif argv == 'is_notword':
            # 否定词典文件存储为字典
            dict_words = {}
            with open(notlist_path, 'r', encoding='utf-8') as f_not:
                lines = f_not.readlines()
                for line in lines:
                    line = line.strip('\n')
                    if line in dict_words:
                        continue
                    else:
                        dict_words[line] = True
            self._notword_dict = dict_words
        else:
            print('未定义该字段')

    def verifyPos(self, keywords):
        """
        筛选关键词中的正向情感词
        :return: 返回正向情感词
        """
        if not self._posword_dict:
            self._creatDict('is_pos')
        # 过滤非正向情感词
        reserve_words = []   # 正向情感词列表
        for keyword in keywords:
            if keyword in self._posword_dict:
                reserve_words.append(keyword)
        return reserve_words

    def verifyNeg(self, keywords):
        """
        筛选关键词中的负向情感词
        :return: 返回负向情感词
        """
        if not self._negword_dict:
            self._creatDict('is_neg')
        # 过滤非负向情感词
        reserve_words = []   # 负向情感词列表
        for keyword in keywords:
            if keyword in self._negword_dict:
                reserve_words.append(keyword)
        return reserve_words

    def filterStopword(self, words):
        """
        过滤停止词
        :return: 返回过滤后的分词结果列表
        """
        if not self._stopword_word:
            self._creatDict('is_stopword')
        # 过滤停止词
        reserve_words = []   # 过滤后分词列表
        for word in words:
            if word in self._stopword_word:
                continue
            reserve_words.append(word)
        return reserve_words

    def filterBlackword(self, words):
        """
        过滤黑名单词
        :return: 返回过滤后的分词结果列表
        """
        if not self._blackword_dict:
            self._creatDict('is_blackword')
        # 过滤黑名单词
        reserve_words = []   # 过滤后分词列表
        for word in words:
            if word in self._blackword_dict:
                continue
            reserve_words.append(word)
        return reserve_words

    def filterSensitiveword(self, words):
        """
        过滤敏感词
        :return: 返回过滤后的分词结果列表
        """
        if not self._sensitiveword_dict:
            self._creatDict('is_sensitiveword')
        # 过滤敏感词
        reserve_words = []   # 过滤后分词列表
        for word in words:
            if word in self._sensitiveword_dict:
                continue
            reserve_words.append(word)
        return reserve_words

    def filterNotword(self, words):
        """
        过滤否定词
        :return: 返回过滤后的分词结果列表
        """
        if not self._notword_dict:
            self._creatDict('is_notword')
        # 过滤否定词
        reserve_words = []
        for word in words:
            if word in self._notword_dict:
                continue
            reserve_words.append(word)
        return reserve_words

    def _setLanguage(self):
        import langid
        # 设置支持中英文检测
        langid.set_languages(['en', 'zh'])
        self._langid = langid

    def langDetection(self, sentences):
        """
        语言检测（中英检测）
        :param sentences:待检测的文本字符串
        :return:zh表示中文，en表示英文
        """
        if not self._langid:
            self._setLanguage()
        # 检测文本语言
        lang_tuple = self._langid.classify(sentences)
        return lang_tuple[0]

if __name__ == "__main__":

    from seg import Seg
    import time
    # text = "萌萌之旅~香港~甜姨姨私房甜品。赞！榴莲豆花[强]，芝麻豆腐西米露[强]。美国travel杂质全球十大甜品。2006地标明星店。  "
    text = "没有中强震@许闯Trunk | 2018摄影封面集#coverfx封面[超话]# 许闯今年不仅为老朋友倪妮/李宇春/angelababy/姚晨拍摄封面，何穗少林禅宗/袁泉/周韵/俞飞鸿/李嫣首封/摄影师陈漫均让人惊喜，还有贝克汉姆/段亦宏/黄渤/陈坤/邓伦/井柏然/邪不压正三人组/蔡徐坤/易烊千玺 等各路男神～ "
    # text = "中强震@许闯[超话]"
    # text = "actually"

    time0 = time.time()
    seg = Seg()
    du = DataUtils()
    time1 = time.time()
    print('实例初始化时间:{}秒'.format(time1 - time0))

    text1 = du.deWeiboHeader(text)
    text1 = du.deUtf8(text1)
    text1 = du.deWeiboEmotion(text1)
    text1 = du.deUrl(text1)
    text1 = du.deSymbol(text1)
    text1 = du.deHandles(text1)
    text1 = du.deLuanma(text1)
    words = seg.lcut(text1)
    print('初次分词结果：')
    print('{}'.format(words))
    time2 = time.time()
    print('第一次分词时间（含加载）:{}秒'.format(time2 - time1))

    words1 = du.deShortWords(words)
    words1 = du.deDigit(words1)
    words1 = du.filterStopword(words1)
    words1 = du.filterBlackword(words1)
    words1 = du.filterSensitiveword(words1)
    words1 = du.filterNotword(words1)
    print('过滤分词结果：')
    print('{}'.format(words1))
    time4 = time.time()
    print('第一次过滤分词时间:{}秒'.format(time4 - time2))
    #
    for i in range(10000):
        words2 = du.deShortWords(words)
        words2 = du.deDigit(words2)
        words2 = du.filterStopword(words2)
        words2 = du.filterBlackword(words2)
        words2 = du.filterSensitiveword(words2)
        words2 = du.filterNotword(words2)
    time5 = time.time()
    print('10000次过滤分词时间:{}秒'.format(time5 - time4))
