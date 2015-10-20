# -*- coding: utf-8 -*-

import weibo
import analyse


def t1():
    try:
        a = weibo.Weibo()
        a.get_hot_posts()
        a.get_person("http://weibo.com/duansimon")
    finally:
        a.close()

def t3():
    analyse.update_type_keywords() # 用来更新类型关键字

    p = analyse.get_person_keywords("1318700490") # 获取用户关键字信息
    print(p)

    p = analyse.analyse_person("1318700490") # 分析用户兴趣类型
    print(p)

t3()
