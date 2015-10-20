#coding=utf-8
# 抓取优设的链接
from lxml.html import fromstring
import urllib.request as request
import sys
import datetime
import pymysql
import time

start_time = datetime.datetime.now()

# 数据库连接信息
config = {
    'user': 'root',
    'passwd': '****',#密码
    'host': '127.0.0.1',
    'db': 'python',
    'charset': 'utf8'
}

# 数据库设计
"""
id
title
url
published_date
time
author_name
author_link
image_link
"""
# sql
'''
create table uisdc(
id int primary key auto_increment,
title varchar(128),
url varchar(256),
published_date varchar(128),
time varchar(64),
author_name varchar(64),
author_link varchar(128),
image_link varchar(256)
)
'''

def insert_info(tmp):
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    sql = "insert into uisdc(title,url,published_date,time,author_name,author_link,image_link) values(%s,%s,%s,%s,%s,%s,%s)"
    cursor.execute(sql, tmp)
    conn.commit()
    cursor.close()
    conn.close()

#测试数据库是否可用
#cha_ru=['nimei','www.baidu.cim','niguan','2012/11/11','melody','meiyou.com','mimei.jpg']
# insert_info(cha_ru)
# sys.exit(0)

url_front = "http://www.uisdc.com/archives/page/"
for pre_ffix in range(1,303):
    real_url=url_front+str(pre_ffix)
    # print(real_url)
    try:
        response=request.urlopen(real_url)
    except:
        print("连接网络失败")
        sys.exit(0)
    doc=response.read()
    html_src=fromstring(doc)
    div=html_src.cssselect(".hfeed>div")
    for i in range(len(div)):
        # title,url,published_date,time,author_name,author_link,image_link
        real_div=div[i]
        title=real_div.cssselect("h2>a")[0].text
        url=real_div.cssselect("h2>a")[0].attrib.get("href")
        published_date=real_div.cssselect("div>abbr")[0].attrib.get("title")
        time_abbr=real_div.cssselect("div>abbr")[0].text
        author_name=real_div.cssselect("span>a")[0].text
        author_link=real_div.cssselect("span>a")[0].attrib.get("href")
        image_link=real_div.cssselect("a>img")[0].attrib.get("src")
        # print(title+"\n"+url+"\n"+published_date+"\n"+time_abbr+"\n"+author_name+"\n"+author_link+"\n"+image_link)
        inser_tmp=[title,url,published_date,time_abbr,author_name,author_link,image_link]
        insert_info(inser_tmp)
        print("第"+str(pre_ffix)+"页的第"+str(i+1)+"个入库成功")

stop_time = datetime.datetime.now()
print("总耗时:"+str(start_time-stop_time))








