#coding=utf-8
__author__ = 'melody'

from lxml.html import fromstring
import urllib.request as request
import sys
import datetime
import pymysql
import time



#sql:
#CREATE TABLE `weibo_rank` (
#  `id` int(11) NOT NULL AUTO_INCREMENT,
# `rank_num` varchar(16) DEFAULT NULL,
#`blog_name` varchar(32) NOT NULL,
#  `blog_url` varchar(128) DEFAULT NULL,
#  `blog_belong` varchar(16) NOT NULL,
#  `visited_num` varchar(16) NOT NULL,
#  PRIMARY KEY (`id`)
#) ENGINE=InnoDB AUTO_INCREMENT=1001 DEFAULT CHARSET=utf8


start_time = datetime.datetime.now()

config = {
    'user': '****',
    'passwd': '****',
    'host': '127.0.0.1',
    'db': '****',
    'charset': 'utf8',
}

def insert_info(tmp):
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    sql = "insert into weibo_rank(rank_num,blog_name,blog_url,blog_belong,visited_num) values(%s,%s,%s,%s,%s)"
    cursor.execute(sql, tmp)
    conn.commit()
    cursor.close()
    conn.close()

url_front = r'http://blog.sina.com.cn/lm/iframe/top/'
suffix = '.html'
preffix = 'alltop_more_new_'
# url_next='alltop_more_new_1.html'
page_num = 1
rank_num = []
blog_name = []
blog_belong = []
blog_url = []
visited_num = []
i = 1
while page_num < 11:

    url_next = preffix + str(page_num) + suffix
    try:
        response = request.urlopen(url_front + url_next)
        time.sleep(1)
    except:
        print(u'连接网络失败')
        response = None
        sys.exit(0)
    doc = response.read().decode('gbk')
    html_src = fromstring(doc)
    tr = html_src.cssselect('tr')[1:]

    for tr_content in tr:
        rank_num.append(tr_content.cssselect('span')[0].text)
        blog_name.append(tr_content.cssselect('a')[0].text)
        blog_belong.append(tr_content.cssselect('a')[1].text)
        blog_url.append(tr_content.cssselect('a')[0].attrib.get('href'))
        # print(page_num,i)
        if page_num == 1 and i <= 3:
            i += 1
            visited_num.append(tr_content.cssselect('font')[0].text.strip())
        else:
            visited_num.append(tr_content.cssselect('td')[-1].text.strip())

    page_num += 1

# rank_num,blog_name,blog_url,blog_belong,visited_num
tmp_list = []
for i in range(len(rank_num)):
    tmp = tuple([rank_num[i], blog_name[i], blog_url[i], blog_belong[i], visited_num[i]])
    tmp_list.append(tmp)
    insert_info(tmp_list[i])
#return tmp_list

end_time = datetime.datetime.now()
#print(len(visited_num))
#print(visited_num[1])

print("run time:{}".format((start_time - end_time).seconds))
