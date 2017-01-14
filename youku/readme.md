##登录优酷获取登录cookie
> 本文以python3为例，Python2的使用方式大同小异。请首先确保已经安装python3和pip

- 安装selenium，可参见[官方文档][1] 
<pre>
sudo pip install -U selenium 
</pre>
- 操作 chrome 浏览器需要有 ChromeDriver ,因此下载chromedriver到<code>/usr/bin</code>目录

开始写代码部分：
<pre>
#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
from selenium import webdriver
import time
def getYKCookie(username,password):
    sel=webdriver.Chrome()
    longurl='https://account.youku.com/'
    sel.get(longurl)
    #设置时间等待网页加载完毕
    time.sleep(5)
    try:
        sel.find_element_by_css_selector("#YT-ytaccount").send_keys(username)
        sel.find_element_by_css_selector("#YT-ytpassword").send_keys(password)
        print('user success!')
    except:
        print("user error!")
    #可根据网络状况调整
    time.sleep(2)
    try:
        sel.find_element_by_css_selector("#YT-nloginSubmit").click()
        print("login success")
    except:
        print("click error")
    #等待登录成功
    time.sleep(4)
    curpage_url = sel.current_url
    print(curpage_url)
    if(curpage_url == longurl):
        print("login error")

    cookie = [item["name"] + "=" + item["value"] for item in sel.get_cookies()]
    cookiestr = ';'.join(item for item in cookie)
    return cookiestr
username='*****'
password='*****'
cookiestr=getYKCookie(username,password)
print(cookiestr)
</pre>



[1]: http://selenium-python.readthedocs.io/installation.html

