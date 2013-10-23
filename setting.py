# -*- coding: utf-8 -*-
from os import environ
#Create = 20120517

YBLOG_VERSION = '20120721' # 当前版本
APP_NAME = environ.get("APP_NAME", "")
debug = not APP_NAME

##下面需要修改
#SITE_TITLE = u"" #博客标题
#SITE_TITLE2 = u"" #显示在边栏上头（有些模板用不到）
#SITE_SUB_TITLE = u"" #副标题
#KEYWORDS = u"宅男 手机 Python SAE GAE 云计算 淘宝" #博客关键字
#SITE_DECR = u"一个宅男的博客，写写程序，谈谈工作，写写生活" #博客描述，给搜索引擎看
#ADMIN_NAME = u"abc" #发博文的作者
#NOTICE_MAIL = u"****@gmail.com" #常用的，容易看到的接收提醒邮件，如QQ 邮箱，仅作收件用

###配置邮件发送信息，提醒邮件用的，必须正确填写，建议用Gmail
#MAIL_FROM = '****@gmail.com'
#MAIL_SMTP = 'smtp.gmail.com'
#MAIL_PORT = 587
#MAIL_PASSWORD = ''
#MAIL_FALG = True#只有gmail才是True

#放在网页底部的统计代码
#ANALYTICS_CODE = """"""
#ADSENSE_CODE1 = """"""
#ADSENSE_CODE2 = """"""

#使用SAE Storage 服务（保存上传的附件），需在SAE管理面板创建
STORAGE_DOMAIN_NAME = 'attachment'

###设置容易调用的jquery 文件
JQUERY = "http://lib.sinaapp.com/js/jquery/1.6.2/jquery.min.js"

COPY_YEAR = '2012' #页脚的 © 2011

MAJOR_DOMAIN = '%s.sinaapp.com' % APP_NAME #主域名，默认是SAE 的二级域名
#MAJOR_DOMAIN = 'www.yourdomain.com'

##博客使用的主题，目前虽然有default/octopress/octopress-disqus，但是只有octopress可用
##你也可以把自己喜欢的wp主题移植过来，或者修改default或者octopress-disqus
#制作方法参见 http://saepy.sinaapp.com/t/49
#以后要在博客设置里设置为皮肤可换
THEME = 'octopress'

#使用disqus 评论系统，如果你使用就填 website shortname，
#申请地址 http://disqus.com/
DISQUS_WEBSITE_SHORTNAME = ''

####友情链接列表，在管理后台也实现了管理，下面的链接列表仍然有效并排在前面
LINK_BROLL = [
    {"text": 'Sina App Engine', "url": 'http://sae.sina.com.cn/'},
]

#当发表新博文时自动ping RPC服务，中文的下面三个差不多了
XML_RPC_ENDPOINTS = [
    'http://blogsearch.google.com/ping/RPC2',
    'http://rpc.pingomatic.com/',
    'http://ping.baidu.com/ping/RPC2'
]

##如果要在本地测试则需要配置Mysql 数据库信息
if debug:
    MYSQL_DB = 'app_saepy'
    MYSQL_USER = 'root'
    MYSQL_PASS = '123'
    MYSQL_HOST_M = '127.0.0.1'
    MYSQL_HOST_S = '127.0.0.1'
    MYSQL_PORT = '3306'

####除了修改上面的设置，你还需在SAE 后台开通下面几项服务：
# 1 初始化 Mysql
# 2 建立一个名为 attachment 的 Storage
# 3 启用Memcache，初始化大小为1M的 mc，大小可以调，日后文章多了，PV多了可增加
# 4 创建一个 名为 default 的 Task Queue
# 详见 http://saepy.sinaapp.com/t/50 详细安装指南
############## 下面不建议修改 ###########################
if debug:
    BASE_URL = 'http://127.0.0.1:8080'
else:
    BASE_URL = 'http://%s'%MAJOR_DOMAIN

LANGUAGE = 'zh-CN'
COMMENT_DEFAULT_VISIBLE = 1 #0/1 #发表评论时是否显示 设为0时则需要审核才显示

GRAVATAR_SUPPORT = 0
COMMENT_EMAIL_REQUIRE = 0 #comment是否需要输入email

EACH_PAGE_POST_NUM = 7 #每页显示文章数
EACH_PAGE_COMMENT_NUM = 10 #每页评论数
RELATIVE_POST_NUM = 5 #显示相关文章数
SHORTEN_CONTENT_WORDS = 150 #文章列表截取的字符数
DESCRIPTION_CUT_WORDS = 100 #meta description 显示的字符数
RECENT_COMMENT_NUM = 5 #边栏显示最近评论数
ADMIN_RECENT_COMMENT_NUM = 10 #在admin界面显示的评论数
RECENT_COMMENT_CUT_WORDS = 20 #边栏评论显示字符数
LINK_NUM = 10 #边栏显示的友情链接数
MAX_COMMENT_NUM_A_DAY = 10 #客户端设置Cookie 限制每天发的评论数
PAGE_CACHE = not debug #本地没有Memcache 服务
COMMON_CACHE_TIME = 3600*24 #通用缓存时间
PAGE_CACHE_TIME   = 3600*24 #默认页面缓存时间
POST_CACHE_TIME   = 3600*24 #默认文章缓存时间
HOT_TAGS_NUM = 30 #右侧热门标签显示数
MAX_ARCHIVES_NUM = 50 #右侧热门标签显示数
MAX_IDLE_TIME = 5 #数据库最大空闲时间 SAE文档说是30 其实更小，设为5，没问题就不要改了

BLOG_PSW_SUPPORT = True #博客支持密码阅读
LINK_BROLL_SUPPORT = False #sidebar是否支持友情链接
BLOG_BACKUP_SUPPORT = False  #是否支持博客备份

NUM_SHARDS = 0 #分片计数器的个数,人少的话用0就可以了，如果由0扩展到比如3，可能程序需要稍微修改一下
if NUM_SHARDS > 0:
    SHARD_COUNT_SUPPORT = True #是否支持分片计数器
else:
    SHARD_COUNT_SUPPORT = False

#MOVE_SECRET = '123456' #迁移博客的密码

DETAIL_SETTING_SUPPORT = False #是否支持详细设置

#微信验证码，这是要在微信后台填的字符串，验证是否拥有网站所有权用的
WX_TOKEN = '123456'
#微信最大显示的文章数
WX_MAX_ARTICLE = 5
#微信文章默认图片
WX_DEFAULT_PIC = "http://yobin-attachment.stor.sinaapp.com/zhaoyang1.jpg"

