#coding=utf-8
# www.wenjian.net的内容
from lxml.html import fromstring
from lxml.etree import tostring
from lxml.html import fragment_fromstring
import urllib.request as request
import sys
import datetime
import csv

start_time = datetime.datetime.now()


# 数据库设计
"""
id
file_name
company
product_name
file_version
file_size
file_path
description
download_url
"""


#由于时间限制，所以只给出每次插入一条的函数
def insert(data):
    with open('test.csv','a+') as csvout:
        writer=csv.writer(csvout)
        writer.writerow(data)


#测试函数insert
# insert(['1','2','3'])
# insert(['4','5','6'])

url_front = "http://www.wenjian.net"
for word in range(105,114):
    for page in range(0,1000):
        full_url=url_front+"/"+str(page)+"/"+chr(word)+".html"
        print("get from:"+full_url)
        try:
            response=request.urlopen(full_url)
        except:
            print("连接网络失败")
            sys.exit(0)

        doc=response.read()
        html_src=fromstring(doc)
        hrefs=html_src.cssselect(".newsList  ul li a")
        datatemp=[]
        for info in hrefs:
            softs=request.urlopen(url_front+info.attrib.get('href')).read().decode('UTF-8')
            soft=fromstring(softs)
            ahrefs=soft.cssselect(".f_title")
            if len(ahrefs)<3:
                break
            downloadurl=soft.cssselect("#f_left >div> span > a")[0].attrib.get("href")
            ahrefs[0].find(".//center").drop_tag()
            ahrefs[0].find(".//img").drop_tag()
            ahrefs[0].find(".//h1").drop_tag()
            for i in range(1,7):
                ahrefs[i].find(".//span").drop_tag()
            tmp=0
            for ahref in ahrefs:
                if tmp==0:
                    tmp=tmp+1
                    datatemp.append(ahref.text.strip())
                if ahref.text.find('公司')>-1:
                    datatemp.append(ahref.text[ahref.text.index(':')+1:60].strip())
                if ahref.text.find('产品名称')>-1:
                    datatemp.append(ahref.text[ahref.text.index(':')+1:60].strip())
                if ahref.text.find('文件版本')>-1:
                    datatemp.append(ahref.text[ahref.text.index(':')+1:60].strip())
                if ahref.text.find('文件大小')>-1:
                    datatemp.append(ahref.text[ahref.text.index(':')+1:60].strip())
                if ahref.text.find('文件路径')>-1:
                    datatemp.append(ahref.text[ahref.text.index(':')+1:60].strip())
                if ahref.text.find('文件描述')>-1:
                    datatemp.append(ahref.text[ahref.text.index(':')+1:60].strip())

            datatemp.append(url_front+downloadurl)
            insert(datatemp)

# for pre_ffix in range(0,1000):
#     real_url=url_front+str(pre_ffix)
#     # print(real_url)
#     try:
#         response=request.urlopen(real_url)
#     except:
#         print("连接网络失败")
#         sys.exit(0)
#     doc=response.read()
#     html_src=fromstring(doc)
#     div=html_src.cssselect(".hfeed>div")
#     for i in range(len(div)):
#         # title,url,published_date,time,author_name,author_link,image_link
#         real_div=div[i]
#         title=real_div.cssselect("h2>a")[0].text
#         url=real_div.cssselect("h2>a")[0].attrib.get("href")
#         published_date=real_div.cssselect("div>abbr")[0].attrib.get("title")
#         time_abbr=real_div.cssselect("div>abbr")[0].text
#         author_name=real_div.cssselect("span>a")[0].text
#         author_link=real_div.cssselect("span>a")[0].attrib.get("href")
#         image_link=real_div.cssselect("a>img")[0].attrib.get("src")
#         # print(title+"\n"+url+"\n"+published_date+"\n"+time_abbr+"\n"+author_name+"\n"+author_link+"\n"+image_link)
#         inser_tmp=[title,url,published_date,time_abbr,author_name,author_link,image_link]
#         insert_info(inser_tmp)
#         print("第"+str(pre_ffix)+"页的第"+str(i+1)+"个入库成功")
#