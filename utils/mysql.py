# coding=utf-8
# 
# Copyright 2018-2020 Algo-group of Suosi Tech Authors.
#
# Author: zhaoli
#

import pymysql
from config import conf

class MySql(object):

    def __init__(self):
        self.host       = conf.getConf('mysql', 'MYSQL_HOST')
        self.port       = conf.getConf('mysql', 'MYSQL_PORT')
        self.user       = conf.getConf('mysql', 'MYSQL_USER')
        self.password   = conf.getConf('mysql', 'MYSQL_PASSWD')
        self.db_name    = conf.getConf('mysql', 'MYSQL_DEFAULT_DB')

        # 打开数据库连接
        self.db = None
        self.db = pymysql.connect(self.host, self.user, self.password, self.db_name)
        # 使用 cursor() 方法创建一个游标对象 cursor
        self.cursor = self.db.cursor()

    def changeDB(self, db_name):
        self.db_name = db_name
        self.db = pymysql.connect(self.host, self.user, self.password, self.db_name)
        # 使用 cursor() 方法创建一个游标对象 cursor
        self.cursor = self.db.cursor()

    def execute(self, sql):
        # 使用 execute() 方法执行 SQL，如果表存在则删除
        ret = self.cursor.execute(sql)
        self.db.commit()
        data = None
        if 'select' in sql or 'SELECT' in sql:
            data = self.cursor.fetchall()
            data = [tuple(d) for d in data]
        return data
             
    def __del__(self):
        # 关闭数据库连接
        if self.db:
            self.db.close()

if __name__ == '__main__':
    db = MySql()
    sql = "select * from word_dict where word='难题'"
    #sql = "insert into word_pos (word, %s) values ('%s', '%s')"%('nh','去:',3)
    #data = db.execute(sql)
    sql = "select nh from word_pos where word='哈哈'"
    data = db.execute(sql)[0][0]
    print(data)
    sql = "update word_pos set nh = %s where word='%s'"%(data+1, '哈哈')
    print(sql)
    db.execute(sql)
