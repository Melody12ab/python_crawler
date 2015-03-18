# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from json import loads
from time import sleep
from urllib.parse import parse_qs, unquote_plus

from selenium.common import exceptions
from selenium.webdriver import Chrome

import model

import logging
logging.basicConfig(level=logging.NOTSET)
bs = lambda src: BeautifulSoup(src)
qs = lambda query, name: parse_qs(query)[name][0]
re_s = re.compile(r"\s{2,}")
r = lambda s: re_s.sub(" ", s)




def convert_time(s):
    if "月" in s:
        t = datetime.today()
        return t.strftime("%Y-") + s.replace("月", "-").replace("日", "")
    elif "今天" in s:
        t = datetime.today()
        return s.replace("今天", t.strftime("%Y-%m-%d "))
    elif " " in s:
        return s
    else:
        t = datetime.today()
        s = int(s.replace("分钟前", ""))
        d = timedelta(minutes=s)
        s = t - d
        return s.strftime("%Y-%m-%d %H:%M")


class Browser:
    def __init__(self):
        self.browser = Chrome(executable_path="D:\Python3.4.0\chromedriver_win32\chromedriver.exe")
        self.browser.set_page_load_timeout(60)

    @property
    def source(self):
        return self.browser.page_source

    @property
    def url(self):
        return self.browser.current_url

    def get(self, url):
        try:
            self.browser.get(url)
        except exceptions.TimeoutException:
            pass
        sleep(5)

    def execute(self, js):
        self.browser.execute_script(js)

    def wait_elem_away(self, selector, text=None):
        while True:
            try:
                elems = self.browser.find_elements_by_css_selector(selector)
                if text is not None:
                    cnt = 0
                    for elem in elems:
                        if elem.text == text:
                            break
                        else:
                            cnt += 1
                    if cnt == len(elems):
                        return
                sleep(5)
            except exceptions.NoSuchElementException:
                return
            except exceptions.StaleElementReferenceException:
                return

    def wait_elem_come(self, selector):
        while True:
            try:
                self.browser.find_element_by_css_selector(selector)
                return
            except exceptions.NoSuchElementException:
                sleep(5)

    def fill_name(self, selector, value):
        self.browser.find_element_by_css_selector(selector).send_keys(value)

    def get_elem(self, selector):
        try:
            return self.browser.find_element_by_css_selector(selector)
        except exceptions.NoSuchElementException:
            return None

    def get_elems(self, selector):
        try:
            return self.browser.find_elements_by_css_selector(selector)
        except exceptions.NoSuchElementException:
            return None
            
    def find_element_by_class_name(self, name, value):
        self.browser.find_elements_by_css_selector(name).send_keys(value)

    def close(self):
        #self.browser.close()
        self.browser.quit()



class Weibo:
    def __init__(self, username="mathwebteam@sina.com", password="mathwebteam"):
        self.br = Browser()
        self.db = model.Database()
        self.re_person = re.compile(
            r"(?ai)weibo\.com/(?P<user_id>u/\d+|[0-9a-z]+)")
        #self.re_topic_post = re.compile(r"(?ai)huati\.weibo\.com/(?P<topic_id>\d+)")
        self.re_post = re.compile(
            r"(?aix)weibo\.com/(?P<user_id>\d+)/(?P<post_id>[0-9a-z]+)")
        self.login(username, password)

    def close(self):
        self.br.close()
        self.db.close()


    def login(self, username, password):
        self.br.get("http://weibo.com") # 开始登录
        self.br.wait_elem_come("#pl_login_form") # 等待登录框出现
        sleep(2)
        self.br.fill_name(".W_login_form .username .W_input", username) # 用户名
        self.br.fill_name(".W_login_form .password .W_input", password) # 密码
        self.br.get_elem(".W_login_form .login_btn .W_btn_g span").click() # 点击登录
        sleep(4) # 等待登录完成


    def check_weibo_type(self):
        if "http://e.weibo.com" in self.br.url:
            self._gen_user_info = self._gen_user_info_e
            self._gen_post_info = self._gen_post_info_e
            self._post_get_reposts = self._post_get_reposts_e
            self._person_get_posts = self._person_get_posts_e
            self._person_load_all_posts = self._person_load_all_posts_e
            self._post_filter_child = self._post_filter_child_e
        else:
            self._gen_user_info = self._gen_user_info_n
            #self._gen_post_info = self._gen_post_info_n
            #self._post_get_reposts = self._post_get_reposts_n
            #self._person_get_posts = self._person_get_posts_n
            #self._person_load_all_posts = self._person_load_all_posts_n
            #self._post_filter_child = self._post_filter_child_n


    def valid_post_url(self, url):
        m = self.re_post.search(url)
        if m:
            user_id = m.group("user_id")
            post_id = m.group("post_id")
            url_tmpl = "http://weibo.com/{}/{}?type=repost"
            return url_tmpl.format(user_id, post_id)
        else:
            return None


    def valid_person_url(self, url):
        m = self.re_person.search(url)
        if m:
            user_id = m.group("user_id")
            url = "http://weibo.com/{}?profile_ftype=1#pl_content_changeLanguage".format(user_id)
            return url
        else:
            return None


    def valid_topic_post_url(self, url):
        m = self.re_topic_post.search(url)
        if m:
            url_tmpl = "http://huati.weibo.com/{}?order=time"
            tid = m.group("topic_id")
            return (url_tmpl.format(tid), tid)
        else:
            return (None, None)


    def _topic_posts_store(self, pair, src):
        data_posts = src.select("#pl_content_topicFeed span.time.W_textc a")
        for data_post in data_posts:
            _, user_id, post_id = data_post["href"].rsplit("/", 2)
            pair.append((user_id, post_id)) # 加入待存储列表


    def _topic_posts_save(self, pair):
        tid, t_name = pair.pop(0)
        url_tmpl = "http://weibo.com/{}/{}"
        for uid, pid in pair:
            self.br.get(url_tmpl.format(uid, pid))
            self.check_weibo_type()
            src = bs(self.br.source)
            post = self._gen_post_info(src)
            self.db.insert_topic_post(tid, t_name, post)


    def _topic_insert(self, src, topic_type):
        # 获取话题
        data_topics = src.select(".topic_list_new .name")
        for data_topic in data_topics:
            topic_id = data_topic["href"].rsplit("/", 1)
            topic_id = unquote_plus(topic_id[1]).strip()
            topic_id=topic_id[0:len(topic_id)-24]
            topic_name = data_topic.get_text().strip("#")
            t = model.Topic(topic_id, topic_name, topic_type)
            self.db.insert_topic(t) # 插入数据


    def _gen_user_info_n(self, src):
        user_name = src.select(".profile_top .pf_name .name")
        if not user_name: return None
        user_name = user_name[0].get_text()
        
        data_id = src.select(".icon_bed .pf_lin")  
        
        if not data_id: return None
        data_id = data_id[0].get_text()
        if "/u/" in data_id:
            user_id = data_id.rsplit("/", 1)[1]
            custom_id = None
        else:
            custom_id = data_id.rsplit("/", 1)[1]            
            data_id = src.select(".icon_bed a")
            
            if not data_id: return None
            user_id = data_id[1]["href"].rsplit("=",1)[1]
            
 
        return model.User(user_id, user_name, custom_id)


    def _gen_user_info_e(self, src):
        data_name = src.select("a.logo_img")
        if not data_name: return None
        data_name = data_name[0]
        user_name = data_name["title"]
        url = data_name["href"]
        if "/u/" in url:
            user_id = url.rsplit("/", 1)[1]
            custom_id = None
        else:
            custom_id = url.rsplit("/", 1)[1]
            data_id = src.select("div.state a.W_btn_b")
            if not data_id: return None
            user_id = qs(data_id[0]["action-data"], "uid")
        return model.User(user_id, user_name, custom_id)


    def _gen_post_info_n(self, src):
        # 获取用户
        user = self._gen_user_info(src)
        if user is None: return None
        # 去除转发
        data_source = src.select("div.WB_media_expand.SW_fun2.S_line1.S_bg1")
        if data_source: data_source[0].extract()
        # post id, post time
        data_id = src.select("a.S_link2.WB_time")
        if not data_id: return None
        data_id = data_id[0]
        pid = data_id["href"].rsplit("/", 1)[1]
        ptime = data_id["title"]
        # 转发次数
        data_repost_cnt = src.select("div.WB_handle a")
        if not data_repost_cnt: return None
        data_repost = data_repost_cnt[1].get_text()
        data_repost = data_repost.replace("转发", "").strip("()")
        repost_count = int(data_repost) if data_repost else 0
        # 是否为转发
        data_is_repost = src.select("div.WB_detail")
        if not data_is_repost: return None
        is_repost = True if "isforward" in data_is_repost[0].attrs else False
        # 微博内容
        data_content = src.select("div.WB_text em")
        if not data_content: return None
        content = data_content[0].get_text()
        # mid
        data_mid = src.select("div.WB_detail > div")
        if not data_mid: return None
        mid = data_mid[0]["mid"]
        return model.Post(user, pid, mid, content,
                          ptime, repost_count, is_repost)


    def _gen_post_info_e(self, src):
        # 获取用户
        user = self._gen_user_info(src)
        if user is None: return None
        # 微博内容
        data_content = src.select("dd.content p em")
        if not data_content: return None
        content = data_content[0].get_text()
        # 转发次数
        data_repost = src.select("p.info.W_linkb.W_textb a")
        if not data_repost: return None
        data_repost = data_repost[0].get_text()
        data_repost = data_repost.replace("转发", "").strip("()")
        repost_count = int(data_repost) if data_repost else 0
        # 是否为转发 及 mid
        data_is_repost = src.select("dl.feed_list.W_no_border")
        if not data_is_repost: return None
        mid = data_is_repost[0]["mid"]
        is_repost = True if "isforward" in data_is_repost[0].attrs else False
        # id
        pid = self.br.url.rsplit("/", 1)[1].split("?", 1)[0]
        # 发布时间
        data_time = src.select("p.info.W_linkb.W_textb")
        if not data_time: return None
        data_time = list(data_time[0].children)[2].replace("来自", "").strip()
        ptime = convert_time(data_time)
        return model.Post(user, pid, mid, content,
                          ptime, repost_count, is_repost)


    def _person_insert_fans(self, src, uid):
        data_users = src.select("div.name")
        for data_user in data_users:
            data_id_and_name = data_user.select("a.W_f14")[0]
            user_name = data_id_and_name.get_text()
            data_id = data_id_and_name["href"]
            if "/u/" in data_id:
                user_id = data_id.rsplit("/", 1)[1]
                custom_id = None
            else:
                custom_id = data_id.rsplit("/", 1)[1]
                user_id = data_id_and_name["usercard"].replace("id=", "")
            user = model.User(user_id, user_name, custom_id)
            self.db.insert_fans(uid, user)


    def _person_insert_follows(self, src, uid):
        data_users = src.select("div.name")
        for data_user in data_users:
            data_id_and_name = data_user.select("a.W_f14")[0]
            user_name = data_id_and_name.get_text()
            data_id = data_id_and_name["href"]
            if "/u/" in data_id:
                user_id = data_id.rsplit("/", 1)[1]
                custom_id = None
            else:
                custom_id = data_id.rsplit("/", 1)[1]
                user_id = data_id_and_name["usercard"].replace("id=", "")
            user = model.User(user_id, user_name, custom_id)
            self.db.insert_follows(uid, user)


    def _person_load_all_posts_a(self, css):
        bottom_js = "window.scrollTo(0, 50000)" # 用于跳转到页面底部
        self.br.execute(bottom_js)
        self.br.wait_elem_away(css, "正在加载，请稍候...")
        sleep(1)
        self.br.execute(bottom_js)
        self.br.wait_elem_away(css, "正在加载，请稍候...")
        sleep(5)


    def _person_load_all_posts_e(self):
        self._person_load_all_posts_a("div.feed_lists span")


    def _person_load_all_posts_n(self):
        self._person_load_all_posts_a("div.WB_feed span")


    def _person_insert_posts_e(self, user, src):
        data_posts = src.select("dl.feed_list.W_linecolor")
        for data_post in data_posts:
            # 去除转发来源
            data_origin = data_post.select("dl.comment")
            if data_origin: data_origin[0].extract()
            # 是否为转发
            is_repost = True if "isforward" in data_post.attrs else False
            # 微博 id 和 发布时间
            data_id_and_time = data_post.select("a.date")
            if not data_id_and_time: continue
            data_id_and_time = data_id_and_time[0]
            public_time = data_id_and_time["title"]
            post_id = data_id_and_time["href"].rsplit("/", 1)[1]
            # 微博内容
            data_content = data_post.select("dd.content p")
            if not data_content: continue
            content = data_content[0].get_text()
            # 获取转发数量
            data_repost = data_post.select("p.info a")
            if not data_repost: continue
            data_repost = data_repost[0]
            data_repost = data_repost.get_text().replace("转发", "")
            repost_count = int(data_repost.strip("()")) if data_repost else 0
            # mid
            mid = qs(data_repost["action-data"], "mid")
            post = model.Post(
                user, post_id, mid, content,
                public_time, repost_count, is_repost)
            self.db.insert_post(post)


    def _person_insert_posts_n(self, user, src):
        data_posts = src.select("div.WB_feed_type.SW_fun")
        for data_post in data_posts:
            # 是否为转发
            is_repost = True if "isforward" in data_post.attrs else False
            # 微博 id 和 发布时间
            data_id_and_time = data_post.select("a.S_link2.WB_time")
            if not data_id_and_time: continue
            data_id_and_time = data_id_and_time[0]
            public_time = data_id_and_time["title"]
            post_id = data_id_and_time["href"].rsplit("/", 1)[1]
            # 微博内容
            data_content = data_post.select("div.WB_text")
            if not data_content: continue
            content = data_content[0].get_text()
            # 获取转发数量
            data_repost = data_post.select("div.WB_handle a")
            if not data_repost: continue
            data_repost = data_repost[-3]
            mid = qs(data_repost["action-data"], "mid")
            data_repost = data_repost.get_text().replace("转发", "")
            repost_count = int(data_repost.strip("()")) if data_repost else 0
            post = model.Post(
                user, post_id, mid, content,
                public_time, repost_count, is_repost)
            self.db.insert_post(post)


    def _person_get_posts_e(self, user, src):
        self._person_insert_posts_e(user, src)
        while True:
            btn_next = self.br.get_elems("div.W_pages a.W_btn_a span")
            if len(btn_next) == 2:
                btn_next[1].click()
            elif len(btn_next) == 1 and \
                    btn_next[0].text == "下一页":
                btn_next[0].click()
            else:
                break # 没下一页 退出循环
            sleep(5)
            self._person_load_all_posts()
            src = bs(self.br.source) # 获取 html
            self._person_insert_posts_e(user, src)


    def _person_get_posts_n(self, user, src):
        #self._person_insert_posts_n(user, src)
        #data_links = src.select("div.W_pages_layer a") # 获取页数
        #if data_links: # 有多页微博
            #url_fix = "#pl_content_changeLanguage" # 用于跳转到页面底部
            # 除去第一页
            #links = (a["href"] + url_fix for a in reversed(data_links[:-1]))
            #for link in links: # 翻页
                #self.br.get(link)
                #self._person_load_all_posts()
                #src = bs(self.br.source) # 获取 html
                #self._person_insert_posts_n(user, src)


        self.br.get_elem("a.PRF_feed_list_more.SW_fun_bg.S_line2").click() # 查看更多微博
        self._person_load_all_posts()#跳到页尾
        src = bs(self.br.source) # 获取 html
        self._person_insert_posts_n(user, src)#插入该页入库
       
        self.br.wait_elem_come("div.W_pages") # 等待分页出现
        data_links = src.select("div.W_pages_layer.S-FIXED a") # 获取页数
        print("获取微博页数")
        #print(data_links)
        
        if data_links: # 有多页微博
            url_fix = "#pl_content_changeLanguage" # 用于跳转到页面底部
            # 除去第一页
            links = (a["href"] + url_fix for a in reversed(data_links[:-1]))
            print("links:")
            print(links)
            for link in links: # 翻页
                print("link:")
                print("http://weibo.com/"+link)
                self.br.get("http://weibo.com/"+link)
                self._person_load_all_posts()
                self._person_load_all_posts()
                src = bs(self.br.source) # 获取 html
                self._person_insert_posts_n(user, src)

    def _post_get_reposts_e(self, src, post):
        while True:
            data_reposts = src.select("span.W_linkb")
            if not data_reposts: break # 没有转发 退出循环
            # 获取转发
            for data_repost in data_reposts:
                data_repost = data_repost.select("a")
                if not data_repost: continue
                url = qs(data_repost[1]["action-data"], "url")
                _, user_id, post_id = url.rsplit("/", 2)
                post.children.append((post_id, user_id))
            # 获取下一页
            data_next_page = src.select("div.W_pages span")
            if len(data_next_page) == 2:
                src = self._post_get_next_page_e(data_next_page[1])
            elif len(data_next_page) == 1 and \
                    data_next_page[0].get_text() == "下一页":
                src = self._post_get_next_page_e(data_next_page[0])
            else:
                break # 没下一页 退出循环


    def _post_get_reposts_n(self, src, post):
        while True:
            data_reposts = src.select("dl.comment_list dd")
            if not data_reposts: break # 没有转发 退出循环
            # 获取转发
            for data_repost in data_reposts:
                data_repost = data_repost.select("div.info a")
                if not data_repost: continue
                url = qs(data_repost[1]["action-data"], "url")
                _, user_id, post_id = url.rsplit("/", 2)
                post.children.append((post_id, user_id))
            # 获取下一页
            data_next_page = src.select("a.btn_page_next")
            if not data_next_page: break # 没下一页 退出循环
            src = self._post_get_next_page_n(data_next_page[0])


    def _post_get_next_page_e(self, src):
        prefix = "http://e.weibo.com/aj/mblog/info/big?"
        url = prefix + src["action-data"]
        # 获取 下页内容
        self.br.get(url)
        src = bs(self.br.source).find("pre")
        data_json = loads(src.get_text())
        sleep(5)
        return bs(data_json["data"]["html"])


    def _post_get_next_page_n(self, src):
        prefix = "http://weibo.com/aj/mblog/info/big?" # 构造 json 地址
        data_url = src.find("span")
        url = prefix + data_url["action-data"]
        # 获取 下页内容
        self.br.get(url)
        src = bs(self.br.source).find("pre")
        data_json = loads(src.get_text())
        sleep(5)
        return bs(data_json["data"]["html"])


    def _post_filter_child_e(self, src, post, all_posts):
        while True:
            data_reposts = src.select("dl.comment_list dd")
            # 没有转发 退出循环
            if not data_reposts: break
            # 获取转发
            for data_repost in data_reposts:
                data_url = src.select("span.W_linkb a")[1]
                data_url = qs(data_url["action-data"], "url")
                _, post_id = data_url.rsplit("/", 1)
                post.children[post_id] = all_posts[post_id]
                all_posts[post_id].parent = post
            # 查找下一页
            data_next_page = src.select("div.W_pages span")
            # 获取下一页
            if len(data_next_page) == 2:
                src = self._post_get_next_page(data_next_page[1])
            elif len(data_next_page) == 1 and \
                    data_next_page[0].get_text() == "下一页":
                src = self._post_get_next_page(data_next_page[0])
            else:
                break # 没下一页 退出循环

    def _post_filter_child_n(self, src, post, all_posts):
        while True:
            data_reposts = src.select("dl.comment_list dd")
            if not data_reposts: break # 没有转发 退出循环
            # 获取转发
            for data_repost in data_reposts:
                data_repost = data_repost.select("div.info a")[1]
                url = qs(data_repost["action-data"], "url")
                _, user_id, post_id = url.rsplit("/", 2)
                if post_id in all_posts:
                    post.children[post_id] = all_posts[post_id]
                    all_posts[post_id].parent = post
            # 查找下一页
            data_next_page = src.select("a.btn_page_next")
            # 没下一页 退出循环
            if not data_next_page: break
            # 获取下一页
            src = self._post_get_next_page(data_next_page[0])


    def _post_gen_path(self, root):
        url_tmpl = "http://weibo.com/{}/{}?type=repost"
        all_posts = {}
        # 遍历处理所有节点
        for post_id, user_id in root.children:
            url = url_tmpl.format(user_id, post_id)
            self.br.get(url)
            self.check_weibo_type() # 微博类型
            src = bs(self.br.source)
            # 获取用户真实资料
            post = self._gen_post_info(src)
            if post is None: continue
            all_posts[post_id] = post
            # 转发的处理
            if post.repost_count != 0:
                self._post_filter_child(src, post, all_posts)
        # 生成新的子节点
        root.children = {}
        for child in all_posts.values():
            if child.parent == root:
                root.children[child.post_id] = child


    def _post_get_origin(self, url):
        self.br.get(url)
        src = bs(self.br.source)
        if "http://e.weibo.com" in self.br.url:
            data_origin = src.select("dd.info span a")
            if data_origin:
                url = data_origin[0]["href"]
                self.br.get(url)
                src = bs(self.br.source)
        else:
            data_origin = src.select("div.WB_handle a.S_func4")
            if data_origin:
                url = "http://weibo.com" + data_origin[0]["href"]
                self.br.get(url)
                src = bs(self.br.source)
        self.check_weibo_type()
        return src


    def get_topic_posts(self, topic_id):
        url_tmpl = "http://huati.weibo.com/{}?order=time"
        url = url_tmpl.format(topic_id)
        self.br.get(url)
        self.br.wait_elem_away("#pl_content_topicFeed span", "正在加载，请稍候...")
        src = bs(self.br.source)
        # 获取话题名
        topic_name = src.select("p.tit.W_linka a")[0].get_text()
        data_pair = [(topic_id, topic_name)] # 存储发言
        self._topic_posts_store(data_pair, src)
        # 获取页数信息
        next_page = self.br.get_elem("a.W_btn_a span")
        if next_page is not None:
            next_page.click() # 翻页
            sleep(5)
            while True:
                self.br.wait_elem_away(
                    "#pl_content_topicFeed span", "正在加载，请稍候...")
                src = bs(self.br.source)
                self._topic_posts_store(data_pair, src)
                # 翻页
                next_page = self.br.get_elems("a.W_btn_a span")
                if len(next_page) != 2: break # 已经是最后一页
                next_page[1].click() # 翻页
        self._topic_posts_save(data_pair) # 插入数据库


    def get_topics(self):
        topic_urls = [
            ("http://huati.weibo.com/?ctg1=99&ctg2=0", "全国热点"),
            ("http://huati.weibo.com/?ctg1=99&ctg2=1", "区域热点"),
            ("http://huati.weibo.com/?ctg1=2", "明星人物"),
            ("http://huati.weibo.com/?ctg1=3", "兴趣"),
            ("http://huati.weibo.com/?ctg1=4", "影视"),
            ("http://huati.weibo.com/?ctg1=5", "情感"),
            ("http://huati.weibo.com/?ctg1=6", "公益"),
            ("http://huati.weibo.com/?ctg1=7", "行业"),
            ("http://huati.weibo.com/?ctg1=8", "生活"),
            ("http://huati.weibo.com/?ctg1=9", "族群"),
            ("http://huati.weibo.com/?ctg1=10", "微博生态"),
            ("http://huati.weibo.com/?ctg1=11", "大杂烩"),
        ]
        url_format = "{}&p={}"
        # 遍历获取所有板块
        for url, topic_type in topic_urls:
            # 获取 html
            self.br.get(url) # 进入页面
            self.br.wait_elem_come("div.topic_list_new") # 等待话题出现
            src = bs(self.br.source) # 获取内容
            self._topic_insert(src, topic_type)
            # 获取页数
            data_pages = src.find("a", class_="W_btn_a")
            if data_pages:
                pages = int(data_pages.previous_sibling.get_text())
                for page in range(2, pages + 1): # 翻页
                    self.br.get(url_format.format(url, page))
                    self.br.wait_elem_come("div.topic_list_new") # 等待话题出现
                    src = bs(self.br.source) # 获取内容
                    self._topic_insert(src, topic_type)


    def get_fans(self, user_id):
        url_tmpl = "http://weibo.com/{}/fans?page={}"
        self.br.get(url_tmpl.format(user_id, 1))
        src = bs(self.br.source)
        self._person_insert_fans(src, user_id)
        data_pages = src.select("div.W_pages.W_pages_comment a.page.S_bg1")
        if (data_pages):
            pages = int(data_pages[-1].get_text()) # 获取页数
            for page in range(2, pages + 1):
                self.br.get(url_tmpl.format(user_id, page))
                src = bs(self.br.source) # 获取内容
                self._person_insert_fans(src, user_id)


    def get_follows(self, user_id):
        url_tmpl = "http://weibo.com/{}/follow?page={}"
        self.br.get(url_tmpl.format(user_id, 1))
        src = bs(self.br.source)
        self._person_insert_follows(src, user_id)
        # FIXME
        data_pages = src.select("div.W_pages.W_pages_comment a.page.S_bg1")
        if data_pages:
            pages = int(data_pages[-1].get_text()) # 获取页数
            for page in range(2, pages + 1):
                self.br.get(url_tmpl.format(user_id, page))
                src = bs(self.br.source) # 获取内容
                self._person_insert_follows(src, user_id)


    def get_person(self, url):
        """获取用户所有微博"""
        """url = self.valid_person_url(url)
        if url is None:
            return None"""
        # 获取页面
        self.br.get(url)
        self.check_weibo_type()
        #self._person_load_all_posts()
        src = bs(self.br.source) # 获取 html
        
        #print(src)
        # 用户基本信息
        user = self._gen_user_info(src)
        if user is None: return
        self.db.insert_user(user) # 插入用户信息
        self._update_person_info(user.user_id)
        
        # 获取所有微博
        """self.br.get(url)
        self.check_weibo_type()
        self._person_load_all_posts()
        src = bs(self.br.source) # 获取 html
        
        print('_person_get_posts')
        self._person_get_posts(user, src)"""
        self.db.update_fetched_time(user.user_id)
        
        
        
    def get_person_simple(self, url):
        """获取用户所有微博"""
        url = self.valid_person_url(url)
        if url is None:
            return None
        # 获取页面
        self.br.get(url)
        self.check_weibo_type()
        self._person_load_all_posts()
        src = bs(self.br.source) # 获取 html
        
        #print(src)
        # 用户基本信息
        user = self._gen_user_info(src)
        if user is None: return
        self.db.insert_user(user) # 插入用户信息
        self._update_person_info(user.user_id)
        
        # 获取所有微博
        #self.br.get(url)
        #self.check_weibo_type()
        #self._person_load_all_posts()
        #src = bs(self.br.source) # 获取 html
        
        #print('_person_get_posts')
        #self._person_get_posts(user, src)
        self.db.update_fetched_time(user.user_id)


    def _update_person_info(self, uid):
        url = "http://account.weibo.com/set/iframe" + uid
        self.br.get(url)
        src = bs(self.br.source)
        data = self._gen_person_info_all(src)
        self.db.update_user_info(uid, **data)

    def _gen_person_info_all(self, src):
        trans = {
            "所在地": "address",
            "性别": "gender",
            "生日": "birthday",
            "博客": "blog",
            "简介": "intro",
            "公司": "company",
            "标签": "tags",
            "大学": "school",
            "感情状况": "family",
            "性取向": "sex",
        }
        data = {}
        infos = src.select("div.pf_item")
        for info in infos:
            name = info.select("div.label")[0].get_text()
            if name not in trans: continue
            name = trans[name]
            if name == "company":
                value = info.select("div.con p")
                data[name] = r(value[0].get_text())
                if len(value) != 1:
                    data["company_addr"] = r(value[1].get_text().replace("地区：", ""))
                if len(value) > 2:
                    data["company_job"] = r(value[2].get_text().replace("职位：", ""))
            elif name == "tags":
                tags = info.select("div.con span.S_func1")
                data[name] = [r(tag.get_text()) for tag in tags]
            elif name == "birthday":
                value = info.select("div.con")[0].get_text()
                if "座" in value:
                    data["constellation"] = r(value)
                else:
                    data[name] = value.replace("年", "-").replace("月", "-").replace("日", "")
            else:
                value = info.select("div.con")[0].get_text()
                data[name] = r(value)
        return data


    def get_post_path(self, url):
        url = self.valid_post_url(url)
        if url is None: # 是否是正确的链接
            return
        # 寻找起始微博
        src = self._post_get_origin(url)
        # 获取 用户信息 及 微博内容 并 插入数据库
        post = self._gen_post_info(src)
        if post is None: return
        # 获取转发
        if post.repost_count > 0:
            post.children = [] # FIXME 需要顺序 之后改回来
            self._post_get_reposts(src, post)
        # 整理层次
        self._post_gen_path(post)
        # 存入数据库
        self.db.insert_post_path(post)


    def get_hot_posts(self):
        url = "http://hot.weibo.com"
        self.br.get(url)
        src = bs(self.br.source)
        data_type = src.select("div.W_main_l a")
        #data_type = "<a href=/?v=1199><i class=hot_ico_video></i>视频</a><a href=/?v=2699><i class=hot_ico_food></i>美食</a><a href=/?v=2799><i class=hot_ico_pet></i>萌宠</a><a href=/?v=1299><i class=hot_ico_finance></i>财经</a><a href=/?v=2099><i class=hot_ico_science></i>科技</a><a href=/?v=1599><i class=hot_ico_fashion></i>时尚</a><a href=/?v=2199><i class=hot_ico_health></i>健康</a><a href=/?v=1499><i class=hot_ico_culture></i>文化</a>"
        data_type_link = ((t["href"], t.get_text()) for t in data_type)
        print(data_type)
        print(data_type_link)
        Flag = False
        for type_id, type_name in data_type_link:
           #if type_id =="/?v=1199":
              #Flag = True
              #if Flag:
                  print(type_id)
                  print(type_name)
                  self._get_hot_post(type_id, type_name)


    def _hot_post_load_all(self):
        code = "window.scrollTo(0, document.body.scrollHeight - 500)"
        while True:
            a = self.br.get_elem("a.notes")
            if a is not None:
                a.click()
                sleep(1)
            elif self.br.get_elem("div.W_loading span"):
                self.br.execute(code)
                sleep(1)
            else:
                break



    def _get_hot_post(self, tid, name):
        post_tmpl = "http://weibo.com/{}/{}"
        url = "http://hot.weibo.com" + tid
        self.br.get(url)
        self._hot_post_load_all()
        src = bs(self.br.source)
        data_posts = src.select("div.WB_detail")
        # 获取微博 id
        pair = []
        for data_post in data_posts:
            data_post_link = data_post.select("a.WB_time")
            if not data_post_link: continue
            data_post_link = data_post_link[0]["href"]
            _, user_id, post_id = data_post_link.rsplit("/", 2)
            pair.append((user_id, post_id))
        # 处理结果
        for uid, pid in pair:
            # 该微博不在数据库中
            if not self.db.has_post(pid):
                self.br.get(post_tmpl.format(uid, pid))
                self.check_weibo_type()
                src = bs(self.br.source)
                post = self._gen_post_info(src)
                if post is None: continue
                self.db.insert_post(post)
            self.db.insert_hot_post(pid, name)

    _map_prov = {
        "不限": ("1000", {
            "不限": "1000",
        }),
        "安徽": ("34", {
            "合肥": "1",
            "芜湖": "2",
            "蚌埠": "3",
            "淮南": "4",
            "马鞍山": "5",
            "淮北": "6",
            "铜陵": "7",
            "安庆": "8",
            "黄山": "10",
            "滁州": "11",
            "阜阳": "12",
            "宿州": "13",
            "巢湖": "14",
            "六安": "15",
            "亳州": "16",
            "池州": "17",
            "宣城": "18",
        }),
        "北京": ("11", {
            "东城区": "1",
            "西城区": "2",
            "崇文区": "3",
            "宣武区": "4",
            "朝阳区": "5",
            "丰台区": "6",
            "石景山区": "7",
            "海淀区": "8",
            "门头沟区": "9",
            "房山区": "11",
            "通州区": "12",
            "顺义区": "13",
            "昌平区": "14",
            "大兴区": "15",
            "怀柔区": "16",
            "平谷区": "17",
            "密云县": "28",
            "延庆县": "29",
        }),
        "重庆": ("50", {
            "万州区": "1",
            "涪陵区": "2",
            "渝中区": "3",
            "大渡口区": "4",
            "江北区": "5",
            "沙坪坝区": "6",
            "九龙坡区": "7",
            "南岸区": "8",
            "北碚区": "9",
            "万盛区": "10",
            "双桥区": "11",
            "渝北区": "12",
            "巴南区": "13",
            "黔江区": "14",
            "长寿区": "15",
            "綦江县": "22",
            "潼南县": "23",
            "铜梁县": "24",
            "大足县": "25",
            "荣昌县": "26",
            "璧山县": "27",
            "梁平县": "28",
            "城口县": "29",
            "丰都县": "30",
            "垫江县": "31",
            "武隆县": "32",
            "忠县": "33",
            "开县": "34",
            "云阳县": "35",
            "奉节县": "36",
            "巫山县": "37",
            "巫溪县": "38",
            "石柱土家族自治县": "40",
            "秀山土家族苗族自治县": "41",
            "酉阳土家族苗族自治县": "42",
            "彭水苗族土家族自治县": "43",
            "江津区": "81",
            "合川区": "82",
            "永川区": "83",
            "南川区": "84",
        }),
        "福建": ("35", {
            "福州": "1",
            "厦门": "2",
            "莆田": "3",
            "三明": "4",
            "泉州": "5",
            "漳州": "6",
            "南平": "7",
            "龙岩": "8",
            "宁德": "9",
        }),
        "甘肃": ("62", {
            "兰州": "1",
            "嘉峪关": "2",
            "金昌": "3",
            "白银": "4",
            "天水": "5",
            "武威": "6",
            "张掖": "7",
            "平凉": "8",
            "酒泉": "9",
            "庆阳": "10",
            "定西": "24",
            "陇南": "26",
            "临夏": "29",
            "甘南": "30",
        }),
        "广东": ("44", {
            "广州": "1",
            "韶关": "2",
            "深圳": "3",
            "珠海": "4",
            "汕头": "5",
            "佛山": "6",
            "江门": "7",
            "湛江": "8",
            "茂名": "9",
            "肇庆": "12",
            "惠州": "13",
            "梅州": "14",
            "汕尾": "15",
            "河源": "16",
            "阳江": "17",
            "清远": "18",
            "东莞": "29",
            "中山": "20",
            "潮州": "51",
            "揭阳": "52",
            "云浮": "53",
        }),
        "广西": ("45", {
            "南宁": "1",
            "柳州": "22",
            "桂林": "3",
            "梧州": "4",
            "北海": "5",
            "防城港": "6",
            "钦州": "7",
            "贵港": "8",
            "玉林": "9",
            "百色": "10",
            "贺州": "11",
            "河池": "12",
            "来宾": "13",
            "崇左": "14",
        }),
        "贵州": ("52", {
            "贵阳": "1",
            "六盘水": "2",
            "遵义": "3",
            "安顺": "4",
            "铜仁": "22",
            "黔西南": "23",
            "毕节": "24",
            "黔东南": "26",
            "黔南": "27",
        }),
        "海南": ("46", {
            "海口": "1",
            "三亚": "2",
            "其他": "90",
        }),
        "河北": ("13", {
            "石家庄": "1",
            "唐山": "2",
            "秦皇岛": "3",
            "邯郸": "4",
            "邢台": "5",
            "保定": "6",
            "张家口": "7",
            "承德": "8",
            "沧州": "9",
            "廊坊": "10",
            "衡水": "11",
        }),
        "黑龙江": ("23", {
            "哈尔滨": "1",
            "齐齐哈尔": "2",
            "鸡西": "3",
            "鹤岗": "4",
            "双鸭山": "5",
            "大庆": "6",
            "伊春": "7",
            "佳木斯": "8",
            "七台河": "9",
            "牡丹江": "10",
            "黑河": "11",
            "绥化": "12",
            "大兴安岭": "27",
        }),
        "河南": ("41", {
            "郑州": "1",
            "开封": "2",
            "洛阳": "3",
            "平顶山": "4",
            "安阳": "5",
            "鹤壁": "6",
            "新乡": "7",
            "焦作": "8",
            "濮阳": "9",
            "许昌": "10",
            "漯河": "11",
            "三门峡": "12",
            "南阳": "13",
            "商丘": "14",
            "信阳": "15",
            "周口": "16",
            "驻马店": "17",
            "济源": "18",
        }),
        "湖北": ("42", {
            "武汉": "1",
            "黄石": "2",
            "十堰": "3",
            "宜昌": "5",
            "襄阳": "6",
            "鄂州": "7",
            "荆门": "8",
            "孝感": "9",
            "荆州": "10",
            "黄冈": "11",
            "咸宁": "12",
            "随州": "13",
            "恩施土家族苗族自治州": "28",
            "仙桃": "29",
            "潜江": "30",
            "天门": "31",
            "神农架": "32",
        }),
        "湖南": ("43", {
            "长沙": "1",
            "株洲": "2",
            "湘潭": "3",
            "衡阳": "4",
            "邵阳": "5",
            "岳阳": "6",
            "常德": "7",
            "张家界": "8",
            "益阳": "9",
            "郴州": "10",
            "永州": "11",
            "怀化": "12",
            "娄底": "13",
            "湘西土家族苗族自治州": "31",
        }),
        "内蒙古": ("15", {
            "呼和浩特": "1",
            "包头": "2",
            "乌海": "3",
            "赤峰": "4",
            "通辽": "5",
            "鄂尔多斯": "6",
            "呼伦贝尔": "7",
            "兴安盟": "22",
            "锡林郭勒盟": "25",
            "乌兰察布盟": "26",
            "巴彦淖尔盟": "28",
            "阿拉善盟": "29",
        }),
        "江苏": ("32", {
            "南京": "1",
            "无锡": "2",
            "徐州": "3",
            "常州": "4",
            "苏州": "5",
            "南通": "6",
            "连云港": "7",
            "淮安": "8",
            "盐城": "9",
            "扬州": "10",
            "镇江": "11",
            "泰州": "12",
            "宿迁": "13",
        }),
        "江西": ("36", {
            "南昌": "1",
            "景德镇": "2",
            "萍乡": "3",
            "九江": "4",
            "新余": "5",
            "鹰潭": "6",
            "赣州": "7",
            "吉安": "8",
            "宜春": "9",
            "抚州": "10",
            "上饶": "11",
        }),
        "吉林": ("22", {
            "长春": "1",
            "吉林": "2",
            "四平": "3",
            "辽源": "4",
            "通化": "5",
            "白山": "6",
            "松原": "7",
            "白城": "8",
            "延边朝鲜族自治州": "24",
        }),
        "辽宁": ("21", {
            "沈阳": "1",
            "大连": "2",
            "鞍山": "3",
            "抚顺": "4",
            "本溪": "5",
            "丹东": "6",
            "锦州": "7",
            "营口": "8",
            "阜新": "9",
            "辽阳": "10",
            "盘锦": "11",
            "铁岭": "12",
            "朝阳": "13",
            "葫芦岛": "14",
        }),
        "宁夏": ("64", {
            "银川": "1",
            "石嘴山": "2",
            "吴忠": "3",
            "固原": "4",
            "中卫": "5",
        }),
        "青海": ("63", {
            "西宁": "1",
            "海东": "21",
            "海北": "22",
            "黄南": "23",
            "海南": "25",
            "果洛": "26",
            "玉树": "27",
            "海西": "28",
        }),
        "山西": ("14", {
            "太原": "1",
            "大同": "2",
            "阳泉": "3",
            "长治": "4",
            "晋城": "5",
            "朔州": "6",
            "晋中": "7",
            "运城": "8",
            "忻州": "9",
            "临汾": "10",
            "吕梁": "23",
        }),
        "山东": ("37", {
            "济南": "1",
            "青岛": "2",
            "淄博": "3",
            "枣庄": "4",
            "东营": "5",
            "烟台": "6",
            "潍坊": "7",
            "济宁": "8",
            "泰安": "9",
            "威海": "10",
            "日照": "11",
            "莱芜": "12",
            "临沂": "13",
            "德州": "14",
            "聊城": "15",
            "滨州": "16",
            "菏泽": "17",
        }),
        "上海": ("31", {
            "黄浦区": "1",
            "卢湾区": "3",
            "徐汇区": "4",
            "长宁区": "5",
            "静安区": "6",
            "普陀区": "7",
            "闸北区": "8",
            "虹口区": "9",
            "杨浦区": "10",
            "闵行区": "12",
            "宝山区": "13",
            "嘉定区": "14",
            "浦东新区": "15",
            "金山区": "16",
            "松江区": "17",
            "青浦区": "18",
            "南汇区": "19",
            "奉贤区": "20",
            "崇明县": "30",
        }),
        "四川": ("51", {
            "成都": "1",
            "自贡": "3",
            "攀枝花": "4",
            "泸州": "5",
            "德阳": "6",
            "绵阳": "7",
            "广元": "8",
            "遂宁": "9",
            "内江": "10",
            "乐山": "11",
            "南充": "13",
            "眉山": "14",
            "宜宾": "15",
            "广安": "16",
            "达州": "17",
            "雅安": "18",
            "巴中": "19",
            "资阳": "20",
            "阿坝": "32",
            "甘孜": "33",
            "凉山": "34",
        }),
        "天津": ("12", {
            "和平区": "1",
            "河东区": "2",
            "河西区": "3",
            "南开区": "4",
            "河北区": "5",
            "红桥区": "6",
            "塘沽区": "7",
            "汉沽区": "8",
            "大港区": "9",
            "东丽区": "10",
            "西青区": "11",
            "津南区": "12",
            "北辰区": "13",
            "武清区": "14",
            "宝坻区": "15",
            "宁河县": "21",
            "静海县": "23",
            "蓟县": "25",
            "滨海新区": "26",
            "保税区": "27",
        }),
        "西藏": ("54", {
            "拉萨": "1",
            "昌都": "21",
            "山南": "22",
            "日喀则": "23",
            "那曲": "24",
            "阿里": "25",
            "林芝": "26",
        }),
        "新疆": ("65", {
            "乌鲁木齐": "1",
            "克拉玛依": "2",
            "吐鲁番": "21",
            "哈密": "22",
            "昌吉": "23",
            "博尔塔拉": "27",
            "巴音郭楞": "28",
            "阿克苏": "29",
            "克孜勒苏": "30",
            "喀什": "31",
            "和田": "32",
            "伊犁": "40",
            "塔城": "42",
            "阿勒泰": "43",
            "石河子": "44",
        }),
        "云南": ("53", {
            "昆明": "1",
            "曲靖": "3",
            "玉溪": "4",
            "保山": "5",
            "昭通": "6",
            "楚雄": "23",
            "红河": "25",
            "文山": "26",
            "思茅": "27",
            "西双版纳": "28",
            "大理": "29",
            "德宏": "31",
            "丽江": "32",
            "怒江": "33",
            "迪庆": "34",
            "临沧": "35",
        }),
        "浙江": ("33", {
            "杭州": "1",
            "宁波": "2",
            "温州": "3",
            "嘉兴": "4",
            "湖州": "5",
            "绍兴": "6",
            "金华": "7",
            "衢州": "8",
            "舟山": "9",
            "台州": "10",
            "丽水": "11",
        }),
        "陕西": ("61", {
            "西安": "1",
            "铜川": "2",
            "宝鸡": "3",
            "咸阳": "4",
            "渭南": "5",
            "延安": "6",
            "汉中": "7",
            "榆林": "8",
            "安康": "9",
            "商洛": "10",
        }),
        "台湾": ("71", {
            "台北市": "1",
            "高雄市": "2",
            "基隆市": "3",
            "台中市": "4",
            "台南市": "5",
            "新竹市": "6",
            "嘉义市": "7",
            "新北市": "8",
            "宜兰县": "9",
            "桃园县": "10",
            "新竹县": "11",
            "苗栗县": "12",
            "台中县": "13",
            "彰化县": "14",
            "南投县": "15",
            "云林县": "16",
            "嘉义县": "17",
            "台南县": "18",
            "高雄县": "19",
            "屏东县": "20",
            "澎湖县": "21",
            "台东县": "22",
            "花莲县": "23",
            "其他": "90",
        }),
        "香港": ("81", {
            "中西区": "2",
            "东区": "3",
            "九龙城区": "4",
            "观塘区": "5",
            "南区": "6",
            "深水埗区": "7",
            "黄大仙区": "8",
            "湾仔区": "9",
            "油尖旺区": "10",
            "离岛区": "11",
            "葵青区": "12",
            "北区": "13",
            "西贡区": "14",
            "沙田区": "15",
            "屯门区": "16",
            "大埔区": "17",
            "荃湾区": "18",
            "元朗区": "19",
            "其他": "1",
        }),
        "澳门": ("82", {
            "花地玛堂区": "2",
            "圣安多尼堂区": "3",
            "大堂区": "4",
            "望德堂区": "5",
            "风顺堂区": "6",
            "氹仔": "7",
            "路环": "8",
            "其他": "1",
        }),
        "海外": ("400", {
            "美国": "1",
            "英国": "2",
            "法国": "3",
            "俄罗斯": "4",
            "加拿大": "5",
            "巴西": "6",
            "澳大利亚": "7",
            "印尼": "8",
            "泰国": "9",
            "马来西亚": "10",
            "新加坡": "11",
            "菲律宾": "12",
            "越南": "13",
            "印度": "14",
            "日本": "15",
            "新西兰": "17",
            "韩国": "18",
            "德国": "19",
            "意大利": "20",
            "爱尔兰": "21",
            "荷兰": "22",
            "瑞士": "23",
            "乌克兰": "24",
            "南非": "25",
            "芬兰": "26",
            "瑞典": "27",
            "奥地利": "28",
            "西班牙": "29",
            "比利时": "30",
            "挪威": "31",
            "丹麦": "32",
            "波兰": "33",
            "阿根廷": "34",
            "白俄罗斯": "35",
            "哥伦比亚": "36",
            "古巴": "37",
            "埃及": "38",
            "希腊": "39",
            "匈牙利": "40",
            "伊朗": "41",
            "蒙古": "42",
            "墨西哥": "43",
            "葡萄牙": "44",
            "沙特阿拉伯": "45",
            "土耳其": "46",
            "其他": "16",
        }),
        "其他": ("100", {
            "不限": "1000",
        }),
    }
    _map_sex = {
        "不限": "0",
        "男": "m",
        "女": "f",
    }
    _map_single = {
        "不限": "0",
        "单身": "1",
        "求交往": "2",
        "暗恋中": "3",
        "暧昧中": "4",
        "恋爱中": "5",
        "订婚": "6",
        "已婚": "7",
        "分居": "8",
        "离异": "9",
        "丧偶": "10",
    }
    _map_blood = {
        "不限": "0",
        "A型": "1",
        "B型": "2",
        "AB型": "3",
        "O型": "4",
    }
    _map_isv = {
        "不限身份": "4",
        "普通用户": "0",
        "V用户": "1",
        "个人V用户": "2",
        "机构V用户": "3",
    }
    _map_age = {
        "不限年龄": "0",
        "18岁以下": "1995-2013",
        "19-22岁": "1991-1994",
        "23-29岁": "1990-1984",
        "30-39岁": "1974-1983",
        "40岁以上": "1973-",
    }
    _map_sexual = {
        "不限": "0",
        "男": "1",
        "女": "2",
        "男女": "3",
    }

    default_conditions = {
        "prov": "北京", # 省
        "city": "不限", # 市
        "sex": "女", # 性别
        "age": "不限年龄", # 年龄
        "tag": "", # 标签（空格分割）
        "scho": "", # 学校
        "comp": "", # 公司
        "single": "不限", # 感情状况
        "sexual": "不限", # 性取向
        "blood": "不限", # 血型
        "isv": "不限身份", # 微博身份
    }

    def _gen_query_url(self, **kwargs):
        conditions = self.default_conditions.copy()
        conditions.update(kwargs)

        query_url = ["http://weibo.com/find/f?type=1&search=1"]

        # 省市
        prov = self._map_prov.get(conditions["prov"], None)
        if not prov:
            prov = "1000"
            city = "1000"
        else:
            city = prov[1].get(conditions["city"], "1000")
            prov = prov[0]
            query_url += ["&prov=", prov, "&city=", city]

        # 性别
        sex = self._map_sex.get(conditions["sex"], "0")
        query_url += ["&sex=", sex]

        # 年龄
        age = self._map_age.get(conditions["age"], "0")
        query_url += ["&age=", age]

        # 个人标签
        tags = conditions["tag"].split()
        if tags:
            for index, tag in enumerate(tags, 1):
                query_url += ["&tag", str(index), "=", tag]

        # 学校
        scho = conditions["scho"]
        if scho: query_url += ["&scho=", scho]

        # 公司
        comp = conditions["comp"]
        if comp: query_url += ["&comp=", comp]

        # 感情状况
        single = self._map_single.get(conditions["single"], "0")
        query_url += ["&single=", single]

        # 性取向
        sexual = self._map_sexual.get(conditions["sexual"], "0")
        query_url += ["&sexual=", sexual]

        # 血型
        blood = self._map_blood.get(conditions["blood"], "0")
        query_url += ["&blood=", blood]

        # 微博身份
        isv = self._map_isv.get(conditions["isv"], "4")
        query_url += ["&isv=", isv]

        return "".join(query_url)


    def find_people(self, **kwargs):
        url = self._gen_query_url(**kwargs)
        print("url"+url)
        
        uid_list = []
        first_page = True
        while url:
            self.br.get(url)
            src = bs(self.br.source)
            data_people = src.select("#pl_find_quickFindUserList li")
            for p in data_people:
                uid = p["data-follow"].split("&")[0].replace("uid=", "")
                uid_list.append(uid)
            next_page = src.select("a.W_btn_a")
            if len(next_page) == 3 or (len(next_page) == 2 and first_page):
                url = "http://weibo.com" + next_page[-2]["href"]
                first_page = False
            else:
                url = None

        for uid in uid_list:
            self.get_person_simple("http://weibo.com/u/" + uid)
                
                
    def advertise(self, url):
	       # 获取页面
	      self.br.get(url)
	      sleep(2)
	      self.br.wait_elem_come("div.btn_bed a.W_btn_c") # 等待发送框出现
	      self.br.get_elem("div.btn_bed a.W_btn_c").click() # 点击发私信
	      # 发送广告
	      self.br.wait_elem_come(".W_layer .content") # 等待发送框出现
	      self.br.find_element_by_class_selector(".WB_webim .sendbox_box .sendbox_area").send_keys("你好,很高兴认识你！") # 用户名
	      #self.br.get_elem("a.WBIM_icon_com.WBIM_iconsend_img").click() # 点击选择文件
	      #src = bs(self.br.source)
	      self.br.get_elem(".WB_webim .WBIM_btn_a:hover span").click() # 点击发送	      
	      #self.db.update_fetched_time(user.user_id)
	     


if __name__ == '__main__':
    a = Weibo("********","******")  
    #http://weibo.com/u/2369862891 http://weibo.com/u/1697535297  http://www.weibo.com/maylose 1228329630 赵晓 http://weibo.com/zhaoxiaolovegod 1195818302 http://weibo.com/duansimon 2584547100
    #a.get_person("http://weibo.com/1648138610") #可用
    #a._update_person_info("1648138610")    #可用（存在部分问题）
    #analyse("1318700490")
    #a.get_fans("1648138610")
    #a.get_follows(user_id)
    #a.get_topics()    #可用
    #a.get_topic_posts("31102")
    #a.get_hot_posts()
    #a.close()
    #a.get_post_path("http://weibo.com/1720084970/zwZAgASzV")
    #a.find_people(prov="北京",city="不限",tag="奢侈品",scho="湘潭大学")
    #a.find_people(sex="不限",prov="不限",city="不限",tag="企业",scho="湘潭大学")
    a.advertise("http://weibo.com/mathwebteam")

