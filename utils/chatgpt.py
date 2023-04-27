#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import openai

VERSION = "2.5"


class ChatSession(object):
    def __init__(self):
        self.history = []

    def add_q_a(self, query, answer):
        if len(query) > 0 and len(answer) > 0:
            self.history.append([query, answer])

    def history_str(self):
        return '\n'.join(['Q:{0}\nA:{1}\n'.format(query, answer) for query, answer in self.history])

    def construct_query_davinci003(self, query):
        return self.history_str() + '\nQ:' + query + '\nA:'

    def construct_query_gpt3Turbo(self, query):
        req = []
        for q, a in self.history:
            req.append({'role': 'user', 'content': q})
            req.append({'role': 'assistant', 'content': a})
        req.append({'role': 'user', 'content': query})
        return req

    def construct_query_plato(self, query):
        context = []
        context_role = []

        for query_item, answer_item in self.history:
            context.append(query_item)
            context_role.append(1)
            context.append(answer_item)
            context_role.append(0)

        context.append(query)
        context_role.append(1)
        return context, context_role


class Davinci003API(object):
    @classmethod
    def get_answer(cls, query):
        for i in range(5):
            answer, query_exception = cls.text_davinci_003(query)
            if not query_exception:
                return answer
            else:
                print(query_exception, color='red')
                time.sleep(1)
        return ''

    @classmethod
    def text_davinci_003(cls, query):
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt="%s" % query,
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
        except (openai.error.RateLimitError, openai.error.APIConnectionError) as e:
            return '', e
        answer = response.choices[0].text
        return answer.strip(), None


class GPT3TurboAPI(object):
    @classmethod
    def get_answer(cls, query):
        for i in range(5):
            answer, query_exception = cls.gpt3_turbo(query)
            if not query_exception:
                return answer
            else:
                print(query_exception, color='red')
                time.sleep(1)
        return ''

    @classmethod
    def gpt3_turbo(cls, query):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=query,
                temperature=0,
            )
        except (openai.error.RateLimitError, openai.error.APIConnectionError) as e:
            return '', e
        answer = response["choices"][0]['message']['content']
        return answer.strip(), None


class ChatGPT():

    def __init__(self, api_key):
        openai.api_key = api_key
        self.fmt = ""

    def set_fmt(self, fmt):
        self.fmt = fmt

    def chat(self, query):
        if self.fmt:
            query = self.fmt % query
        session = ChatSession()
        api = GPT3TurboAPI()
        ret = session.construct_query_gpt3Turbo(query)
        ans = api.get_answer(ret)
        return ans

if __name__ == '__main__':
    gpt = ChatGPT('sk-xxx')
    ret = gpt.chat("今天天气怎么样")
    print(ret)
