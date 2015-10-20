# coding=utf-8
import pymysql
from lxml.html import fromstring
import urllib.request as request
import sys

# 品名，类别,价格，网址
# 1.拿到一页里面所有的商品链接
# 2.每一个每一个商品链接单独抓取信息
#3.存储信息
# CREATE TABLE `good_info` (
#   `first_class` varchar(64) DEFAULT NULL,
#   `second_class` varchar(64) DEFAULT NULL,
#   `good_name` varchar(128) DEFAULT NULL,
#   `good_price` varchar(16) DEFAULT NULL,
#   `good_url` varchar(128) DEFAULT NULL
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8


base_url = r'http://www.mygeek.cn/'
preffix = r'Product/new-'
suffix = '.html'
#数据库配置信息
config = {
    'user': '****',
    'passwd': '****',
    'host': '127.0.0.1',
    'db': '****',
    'charset': 'utf8',
}

#插入数据库
def insert_info(tmp_tuple):
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    sql = "insert into good_info values(%s,%s,%s,%s,%s)"
    cursor.execute(sql, tmp_tuple)
    conn.commit()
    cursor.close()
    conn.close()


#取得每个页面所有的商品的url
def getUrlFromUrl(url):
    try:
        response = request.urlopen(url)
    except:
        print(u'连接失败')
        sys.exit(0)
    doc = response.read().decode('gbk')
    html_src = fromstring(doc)
    table = html_src.cssselect('.all_c_d table table')[2:]
    href_list = [href.cssselect('a')[0] for href in table]
    href_attr = [attr.get('href')[3:] for attr in href_list]
    page_url = [base_url + url_tmp for url_tmp in href_attr]
    return page_url


#取得商品的完整url
def getAllUrl(root_url):
    tmp_url = []
    for i in range(14):
        comp_url = base_url + preffix + str(i + 1) + suffix
        tmp_url.extend(getUrlFromUrl(comp_url))
    return tmp_url


#获取想要的信息 品名，类别,价格，网址
# def getDataFromUrlAndSave(*data_url):
#     first_class_list = []
#     second_class_list = []
#     good_name_list=[]
#     good_price_list=[]
#     print(len(data_url))
#     for real_url in data_url:
#         doc = request.urlopen(real_url).read().decode('gbk')
#         html_src = fromstring(doc)
#         first_class = html_src.cssselect('div:nth-child(2) table a:nth-child(3)')[0].text.strip()
#         second_class = html_src.cssselect('div:nth-child(2) table a:nth-child(4)')[0].text.strip()
#         good_name=html_src.cssselect('h1')[0].text.strip()
#         good_price=html_src.cssselect('div:nth-child(2) span')[0].text.strip()[1:]
#         first_class_list.append(first_class)
#         second_class_list.append(second_class)
#         good_name_list.append(good_name)
#         good_price_list.append(good_price)
#         tmp_list=[]
#         for i in range(len(good_price_list)):
#             tmp=tuple([first_class_list[i],second_class_list[i],good_name[i],good_price[i],data_url[i]])
#             tmp_list.append(tmp)
#         insert_info(tmp_list)

def getDataFromUrlAndSave(data_url):
    doc = request.urlopen(real_url).read().decode('gbk')
    html_src = fromstring(doc)
    first_class = html_src.cssselect('div:nth-child(2) table a:nth-child(3)')[0].text.strip()
    second_class = html_src.cssselect('div:nth-child(2) table a:nth-child(4)')[0].text.strip()
    good_name = html_src.cssselect('h1')[0].text.strip()
    good_price = html_src.cssselect('div:nth-child(2) span')[0].text.strip()[1:]
    tmp_list = [first_class, second_class, good_name, good_price, data_url]
    insert_info(tmp_list)


all_url = getAllUrl(base_url)
tmp_i=0
for real_url in all_url:
    tmp_i+=1
    print(u'成功保存%d记录' % tmp_i)
    getDataFromUrlAndSave(real_url)
