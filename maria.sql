

CREATE TABLE weibo_users ( -- 用户表
	id VARCHAR(15) NOT NULL, -- 微博 id
	custom_id VARCHAR(30), -- 自定义的 id
	user_name VARCHAR(30) NOT NULL, -- 用户名
	fetched_time DATETIME NOT NULL DEFAULT "0000-00-00 00:00:00", -- 抓取微博的时间
	address VARCHAR(30), -- 所在地
	gender VARCHAR(1), -- 性别
	birthday DATE, -- 生日
	blood VARCHAR(1), -- 血型
	constellation VARCHAR(3), -- 星座
	blog VARCHAR(100), -- 博客地址
	intro VARCHAR(70), -- 简介
	company VARCHAR(100), -- 公司
	company_addr VARCHAR(30), -- 公司地址
	company_job VARCHAR(30), -- 职务
	school VARCHAR(100), -- 毕业院校
	family VARCHAR(10), -- 感情状况
	sex VARCHAR(10), -- 性取向
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE weibo_user_tags ( -- 用户标签
	user_id VARCHAR(15) NOT NULL,
	tag VARCHAR(20) not null,
	FOREIGN KEY (user_id) REFERENCES weibo_users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE weibo_posts ( -- 微博表
	id VARCHAR(20) NOT NULL, -- 微博 id
    mid VARCHAR(20) NOT NULL, -- mid
	user_id VARCHAR(15) NOT NULL, -- 用户 id
	content TEXT CHARACTER SET utf8 NOT NULL, -- 微博内容 140 字是多大
	public_time DATETIME NOT NULL, -- 发布时间 精确到分钟
	repost_count INT NOT NULL, -- 转发数量
	is_repost BOOL NOT NULL DEFAULT 0, -- 是否为转发
	PRIMARY KEY (id),
	FOREIGN KEY (user_id) REFERENCES weibo_users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE weibo_topics ( -- 话题表
	id VARCHAR(30) NOT NULL, -- 话题 id
	name VARCHAR(100) NOT NULL, -- 话题名
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



CREATE TABLE weibo_user_follow ( -- 关注关系表 多对多
	user_id VARCHAR(15) NOT NULL, -- 用户 id
	follow_id VARCHAR(15) NOT NULL, -- 关注的 id
	FOREIGN KEY (user_id) REFERENCES weibo_users (id),
	FOREIGN KEY (follow_id) REFERENCES weibo_users (id),
	UNIQUE (user_id, follow_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



CREATE TABLE weibo_post_repost ( -- 转发来源关系表 一对多
	repost_id VARCHAR(20) NOT NULL, -- 转发 id
	parent_id VARCHAR(20) NOT NULL, -- 来源 id
	FOREIGN KEY (repost_id) REFERENCES weibo_posts (id),
	FOREIGN KEY (parent_id) REFERENCES weibo_posts (id),
	PRIMARY KEY (repost_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



CREATE TABLE weibo_hot_posts ( -- 热门微博表
	post_id VARCHAR(20) NOT NULL, -- 微博 id
	type_name VARCHAR(20) NOT NULL, -- 板块名
	hot_time DATETIME NOT NULL, -- 收录日期
	FOREIGN KEY (post_id) REFERENCES weibo_posts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



CREATE TABLE weibo_topic_time ( -- 话题时间关系表 多对多
	topic_id VARCHAR(30) NOT NULL, -- 话题
	topic_type VARCHAR(10) NOT NULL, -- 哪个板块
	hot_time DATE NOT NULL, -- 收录时间 精确到天
	FOREIGN KEY (topic_id) REFERENCES weibo_topics (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



CREATE TABLE weibo_topic_post ( -- 话题微博关系表 一对多
	topic_id VARCHAR(30) NOT NULL, -- 话题 id
	post_id VARCHAR(20) NOT NULL, -- 微博 id
	FOREIGN KEY (topic_id) REFERENCES weibo_topics (id),
	FOREIGN KEY (post_id) REFERENCES weibo_posts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
