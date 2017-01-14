#!/usr/local/bin/python3
# -*- coding: utf-8 -*-


from selenium import webdriver
import time

def getYKCookie(username,password):
    sel=webdriver.Chrome()
    longurl='https://account.youku.com/'
    sel.get(longurl)
    time.sleep(10)
    try:
        sel.find_element_by_css_selector("#YT-ytaccount").send_keys(username)
        sel.find_element_by_css_selector("#YT-ytpassword").send_keys(password)
        print('user success!')
    except:
        print("user error!")

    time.sleep(3)

    try:
        sel.find_element_by_css_selector("#YT-nloginSubmit").click()
        print("login success")
    except:
        print("click error")
        
    time.sleep(8)

    curpage_url = sel.current_url
    print(curpage_url)

    if(curpage_url == longurl):
        print("login error")
        
    cookie = [item["name"] + "=" + item["value"] for item in sel.get_cookies()]
    cookiestr = ';'.join(item for item in cookie)
    return cookiestr

username='357170967@qq.com'
password='zx8868108//'

cookiestr=getYKCookie(username,password)
print(cookiestr)
