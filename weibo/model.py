# -*- coding: utf-8 -*-

from datetime import date
import logging
import mysql.connector



class User:
    def __init__(self, user_id, user_name, custom_id):
        self.user_id = user_id
        self.user_name = user_name
        self.custom_id = custom_id


class Post:
    def __init__(self, user, post_id, post_mid, content,
                 public_time, repost_count, is_repost):
        self.user = user
        self.post_id = post_id
        self.post_mid = post_mid
        self.content = content
        self.repost_count = repost_count
        self.is_repost = is_repost
        self.public_time = public_time
        self.parent = None
        self.children = {}


class Topic:
    def __init__(self, topic_id, topic_name, topic_type):
        self.topic_id = topic_id
        self.topic_name = topic_name
        self.topic_type = topic_type
        self.topic_time = date.today().strftime("%Y-%m-%d")




class Connection:
    """ usage:
    >>> import database
    >>> db = database.Connection("user", "password", "database")
    """
    def __init__(self, user, password, database, host="127.0.0.1",
                 connect_timeout=10, time_zone="+0:00"):
        self.host = host

        config = {
            "user": user,
            "password": password,
            "database": database,
            "connect_timeout": connect_timeout,
            "time_zone": time_zone,
            "autocommit": True,
            "sql_mode": "TRADITIONAL",
            "use_unicode": True,
            "charset": "utf8",
        }

        if "/" in host:
            config["unix_socket"] = host
        else:
            pair = host.split(":")
            if len(pair) == 2:
                config["host"] = pair[0]
                config["port"] = int(pair[1])
            else:
                config["host"] = host

        self._db = None
        self._db_config = config

        try:
            self.reconnect()
        except Exception:
            logging.error("Cannot connect to MySQL on {}".format(self.host),
                          exc_info=True)


    def __del__(self):
        self.close()


    def close(self):
        """Closes database connection"""
        if getattr(self, "_db", None) is not None:
            self._db.close()
            self._db = None


    def reconnect(self):
        """Closes the existing database connection and re-opens it"""
        self.close()
        self._db = mysql.connector.connect(**self._db_config)


    def _ensure_connected(self):
        if self._db is None or not self._db.is_connected():
            self.reconnect()


    def _cursor(self):
        self._ensure_connected()
        return self._db.cursor()


    def _execute(self, cursor, query, parameters, kwparameters):
        try:
            return cursor.execute(query, kwparameters or parameters)
        except mysql.connector.OperationalError:
            logging.error("Error connecting to MySQL on {}".format(self.host))
            self.close()
            raise


    def iter(self, query, *parameters, **kwparameters):
        """Returns an iterator for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters, kwparameters)
            for row in cursor:
                yield Row(zip(cursor.column_names, row))
        finally:
            cursor.close()


    def query(self, query, *parameters, **kwparameters):
        """Returns a row list for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters, kwparameters)
            return [Row(zip(cursor.column_names, row)) for row in cursor]
        finally:
            cursor.close()


    def get(self, query, *parameters, **kwparameters):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters, **kwparameters)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for database.get() query")
        else:
            return rows[0]


    def execute(self, query, *parameters, **kwparameters):
        """Executes the given query, returning the rowcount from the query."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters, kwparameters)
            return cursor.rowcount
        finally:
            cursor.close()


    def executemany(self, query, parameters):
        """Executes the given query against all the given param sequences.
        return the rowcount from the query.
        """
        cursor = self._cursor()
        try:
            cursor.executemany(query, parameters)
            return cursor.rowcount
        finally:
            cursor.close()




class Row(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)



class Database:
    def __init__(self):
        config = {
            "user": "root",
            "password": "199429",
            "database": "weibo",
        }
        self.db = Connection(**config)
        
        #self.db = mysql.connector.connect(user='root', password='123456',host='127.0.0.1',database='robotengine',charset='utf8')
        #self.cursor = self.db.cursor(buffered=False)


    def close(self):
        self.db.close()


    def has_post(self, post_id):
        query = "SELECT id FROM weibo_posts WHERE id=%s LIMIT 1"
        if self.db.get(query, post_id) is not None:
            return True
        else:
            return False


    def insert_hot_post(self, post_id, type_name):
        insert = """INSERT INTO weibo_hot_posts (post_id, type_name, hot_time)
            VALUES (%s, %s, NOW())"""
        self.db.execute(insert, post_id, type_name)


    def _insert_topic(self, tid, name):
        query = "SELECT id FROM weibo_topics WHERE id=%s LIMIT 1"
        insert = "INSERT INTO weibo_topics (id, name) VALUES (%s, %s)"
        if self.db.get(query, tid) is None:
            self.db.execute(insert, tid, name)


    def insert_topic_post(self, tid, tname, post):
        self._insert_topic(tid, tname)
        self.insert_post(post)
        query = """SELECT topic_id FROM weibo_topic_post
            WHERE topic_id=%s AND post_id=%s LIMIT 1"""
        insert = """INSERT INTO weibo_topic_post (topic_id, post_id)
            VALUES (%s, %s)"""
        self.cursor.execute(query, tid, post.post_id)
        if self.db.get(query, tid, post.post_id) is None:
            self.db.execute(insert, tid, post.post_id)


    def insert_topic(self, topic):
        self._insert_topic(topic.topic_id, topic.topic_name)

        query = """SELECT topic_id FROM weibo_topic_time
            WHERE topic_id=%s AND topic_type=%s AND hot_time=%s LIMIT 1"""
        insert = """INSERT INTO weibo_topic_time
            (topic_id, topic_type, hot_time) VALUES (%s, %s, %s)"""

        r = self.db.get(
            query, topic.topic_id, topic.topic_type, topic.topic_time)
        if r is None:
            self.db.execute(
                insert, topic.topic_id, topic.topic_type, topic.topic_time)


    def update_fetched_time(self, user_id):
        update = "UPDATE weibo_users SET fetched_time=NOW() WHERE id=%s"
        self.db.execute(update, user_id)


    def insert_user(self, user):
        query = "SELECT id FROM weibo_users WHERE id=%s LIMIT 1"
        insert = """INSERT INTO weibo_users (id, custom_id, user_name)
            VALUES (%s, %s, %s)"""

        if self.db.get(query, user.user_id) is None:
            self.db.execute(
                insert, user.user_id, user.custom_id, user.user_name)


    def insert_post(self, post):
        query = "SELECT id FROM weibo_posts WHERE id=%s LIMIT 1"
        insert = """INSERT INTO weibo_posts
            (id, mid, user_id, content, public_time, repost_count, is_repost)
            values (%s, %s, %s, %s, %s, %s, %s)"""

        self.insert_user(post.user)
        if self.db.get(query, post.post_id) is None:
            self.db.execute(
                insert,
                post.post_id, post.post_mid, post.user.user_id, post.content,
                post.public_time, post.repost_count, post.is_repost
            )
            return False
        else:
            return True # already existed


    def insert_follows(self, user_id, user):
        self.insert_user(user)
        self._insert_user_follow(user_id, user.user_id)


    def insert_fans(self, user_id, user):
        self.insert_user(user)
        self._insert_user_follow(user.user_id, user_id)


    def _insert_user_follow(self, user_id, follow_id):
        query = """SELECT user_id FROM weibo_user_follow
            WHERE user_id=%s AND follow_id=%s LIMIT 1"""
        insert = """INSERT INTO weibo_user_follow
            (user_id, follow_id) VALUES (%s, %s)"""

        if self.db.get(query, user_id, follow_id) is None:
            self.db.execute(insert, user_id, follow_id)


    def insert_post_path(self, post, parent=None):
        self.insert_post(post)
        if parent:
            query = """SELECT repost_id FROM weibo_post_repost
                WHERE repost_id=%s LIMIT 1"""
            insert = """INSERT INTO weibo_post_repost (repost_id, parent_id)
                VALUES (%s, %s)"""

            if self.db.get(query, post.post_id) is None:
                self.db.execute(insert, post.post_id, parent.post_id)
            for child in post.children.values():
                self.insert_post_path(child, post)
        else:
            for child in post.children.values():
                self.insert_post_path(child, post)


    def query_post(self, uid):
        query = """SELECT content, public_time
            FROM weibo_posts WHERE user_id=%s"""
        return self.db.query(query, uid)


    def query_post_average(self):
        query = """SELECT AVG(c) average FROM
            (SELECT COUNT(*) c FROM weibo_posts GROUP BY user_id) AS tbl"""
        return self.db.get(query)


    def query_hot_post(self):
        query = """SELECT p.content, hp.type_name, hp.hot_time
            FROM weibo_posts p, weibo_hot_posts hp
            WHERE p.id = hp.post_id"""
        return self.db.query(query)


    def query_hot_post_count(self):
        query = """SELECT DISTINCT type_name type, count(post_id) cnt
            FROM weibo_hot_posts GROUP BY type_name"""
        return self.db.query(query)


    def update_type_keywords(self, d):
        delete = """DELETE FROM weibo_hot_keywords"""
        self.db.execute(delete)

        update = """INSERT INTO weibo_hot_keywords(type_name, keyword, score)
            VALUES (%s, %s, %s)"""
        data = []
        for k, v in d.items():
            data += [(k, w, s) for w, s in v.items()]
        self.db.executemany(update, data)

    def query_type_keywords(self):
        query = """SELECT type_name, keyword, score FROM weibo_hot_keywords"""
        return self.db.query(query)

    def update_user_info(self, uid, address=None, gender=None, birthday=None,
                         blood=None, constellation=None, blog=None, intro=None,
                         company=None, company_addr=None, company_job=None,
                         sex=None, family=None, school=None, tags=None):
        update = """UPDATE weibo_users SET
            address=%s,gender=%s,birthday=%s,blood=%s,constellation=%s,
            blog=%s,intro=%s,company=%s,company_addr=%s,company_job=%s,
            school=%s,family=%s,sex=%s
            WHERE id=%s"""
        self.db.execute(update, address, gender, birthday, blood,
                        constellation, blog, intro, company, company_addr,
                        company_job, school, family, sex, uid)
        if tags:
            insert = """INSERT INTO weibo_user_tags(user_id, tag)
                VALUES(%s, %s)"""
            data = []
            for tag in tags:
                data.append((uid, tag))
            self.db.executemany(insert, data)
