#!/usr/bin/env python3.3
# -*- coding: utf-8 -*-

from datetime import datetime
import math
import re

from jieba.analyse import extract_tags

from model import Database


db = Database()

replaces = [
    re.compile(r"(?i)@[^ :]+(?=( |:|@|$))"), # @xxx
    re.compile(r"(?i)http://t.cn/[0-9a-z]{7}"), # http://t.cn/xxx
    re.compile(r"转发微博"),
    re.compile(r"#[^#]+#"), # tag
    re.compile(r"(2[1234]|1?[0-9]):[0-5][0-9]"), # time
]


def cut(s):
    for r in replaces:
        s = r.sub("", s)
    return extract_tags(s, 10)




def update_type_keywords():
    """更新类型关键字"""
    # 计算平均数量
    cnt = db.query_hot_post_count()
    count = {c["type"]: c["cnt"] for c in cnt}
    average = sum(c for c in count.values()) / len(count)

    # 计算关键字
    d = {}
    posts = db.query_hot_post()
    for post in posts:
        type_name = post["type_name"]
        wd = d.setdefault(type_name, {})
        words = cut(post["content"])
        for word in words:
            score = decay(post["hot_time"], 1, average, count[type_name])
            wd[word.lower()] = wd.get(word.lower(), 0) + score

    # 取前 300 个关键字
    dd = {}
    for k, v in d.items():
        s = sorted(v.items(), key=lambda x: x[1], reverse=True)
        dd[k] = dict(s[:300])

    db.update_type_keywords(dd)




def decay(t, a, c, d):
    """ t 时间
    a 衰减的速率，时间的作用与 a 成正比
    c 平均数据量
    d 用户数据量
    """
    b = math.log(d + 1, c)
    return 1 / (a * b * (datetime.now() - t).total_seconds() / 86400 + 1)



def get_person_keywords(uid):
    posts = db.query_post(uid)

    avg = db.query_post_average()["average"]
    l = len(posts)

    d = {}
    for post in posts:
        words = cut(post["content"])
        for word in words:
            d[word] = d.get(word, 0) + decay(post["public_time"], 1, avg, l)

    return d



def analyse_person(uid):
    type_keywords = db.query_type_keywords()

    tt = {x["type_name"] for x in type_keywords}
    rate = 1 / len(tt)
    p = {t: rate for t in tt}

    person_keywords = get_person_keywords(uid)

    for kw, score in person_keywords.items():
        r = ((type_kw["type_name"], type_kw["score"])
             for type_kw in type_keywords if type_kw["keyword"] == kw)
        for type_name, s in r:
            p[type_name] += s * score

    a = sum(p.values())
    return {k: v / a for k, v in p.items()}
