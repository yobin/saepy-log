# -*- coding: utf-8 -*-

import logging
import json
from hashlib import md5
from time import time

from setting import *
from common import *
from model import Article, Comment, Link, Category, Tag, Archive

#yobin 20131023 for weixin begin
from wechat import WeiXin
import urllib2,urllib
import tornado.wsgi
import tornado.escape
#yobin 20131023 for weixin end

###############
class HomePage(BaseHandler):
    @pagecache()
    def get(self):
        try:
            objs = Article.get_post_for_homepage()
        except:
            self.redirect('/install')
            return
        if objs:
            fromid = objs[0].id
            endid = objs[-1].id
        else:
            fromid = endid = ''

        allpost =  Article.count_all_post()
        allpage = allpost/EACH_PAGE_POST_NUM
        if allpost%EACH_PAGE_POST_NUM:
            allpage += 1

        output = self.render('index.html', {
            'title': "%s - %s"%(getAttr('SITE_TITLE'),getAttr('SITE_SUB_TITLE')),
            'keywords':getAttr('KEYWORDS'),
            'description':getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': allpage,
            'listtype': 'index',
            'fromid': fromid,
            'endid': endid,
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
        },layout='_layout.html')
        self.write(output)
        return output

class IndexPage(BaseHandler):
    @pagecache('post_list_index', PAGE_CACHE_TIME, lambda self,direction,page,base_id: page)
    def get(self, direction = 'next', page = '2', base_id = '1'):
        if page == '1':
            self.redirect(BASE_URL)
            return
        objs = Article.get_page_posts(direction, page, base_id)
        if objs:
            if direction == 'prev':
                objs.reverse()
            fromid = objs[0].id
            endid = objs[-1].id
        else:
            fromid = endid = ''

        allpost =  Article.count_all_post()
        allpage = allpost/EACH_PAGE_POST_NUM
        if allpost%EACH_PAGE_POST_NUM:
            allpage += 1
        output = self.render('index.html', {
            'title': "%s - %s | Part %s"%(getAttr('SITE_TITLE'),getAttr('SITE_SUB_TITLE'), page),
            'keywords':getAttr('KEYWORDS'),
            'description':getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': int(page),
            'allpage': allpage,
            'listtype': 'index',
            'fromid': fromid,
            'endid': endid,
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
        },layout='_layout.html')
        self.write(output)
        return output

class PostDetailShort(BaseHandler):
    @client_cache(600, 'public')
    def get(self, id = ''):
        obj = Article.get_article_by_id_simple(id)
        if obj:
            self.redirect('%s/topic/%d/%s'% (BASE_URL, obj.id, obj.title), 301)
            return
        else:
            self.redirect(BASE_URL)

class PostDetail(BaseHandler):
    @pagecache('post', POST_CACHE_TIME, lambda self,id,title: id)
    def get(self, id = '', title = ''):
        tmpl = ''
        obj = Article.get_article_by_id_detail(id)
        if not obj:
            self.redirect(BASE_URL)
            return
        #redirect to right title
        try:
            title = unquote(title).decode('utf-8')
        except:
            pass
        if title != obj.slug:
            self.redirect(obj.absolute_url, 301)
            return
        #
        if obj.password and THEME == 'default':
            rp = self.get_cookie("rp%s" % id, '')
            if rp != obj.password:
                tmpl = '_pw'
        elif obj.password and BLOG_PSW_SUPPORT:
            rp = self.get_cookie("rp%s" % id, '')
            print 'rp===%s' % (str(rp))
            if rp != obj.password:
                tmpl = '_pw'

        keyname = 'pv_%s' % (str(id))
        increment(keyname)#yobin 20120701
        self.set_cookie(keyname, '1', path = "/", expires_days =1)
        self.set_header("Last-Modified", obj.last_modified)
        output = self.render('page%s.html'%tmpl, {
            'title': "%s - %s"%(obj.title, getAttr('SITE_TITLE')),
            'keywords':obj.keywords,
            'description':obj.description,
            'obj': obj,
            'cobjs': obj.coms,
            'postdetail': 'postdetail',
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': 10,
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'hits':get_count(keyname),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
            'listtype': '',
        },layout='_layout.html')
        self.write(output)

        if obj.password and BLOG_PSW_SUPPORT:
            return output
        elif obj.password and THEME == 'default':
            return
        else:
            return output

    def post(self, id = '', title = ''):
        action = self.get_argument("act")

        if action == 'inputpw':
            wrn = self.get_cookie("wrpw", '0')
            if int(wrn)>=10:
                self.write('403')
                return

            pw = self.get_argument("pw",'')
            pobj = Article.get_article_by_id_simple(id)
            wr = False
            if pw:
                if pobj.password == pw:
                    clear_cache_by_pathlist(['post:%s'%id])#yobin 20120630
                    self.set_cookie("rp%s" % id, pobj.password, path = "/", expires_days =1)
                else:
                    wr = True
            else:
                wr = True
            if wr:
                wrn = self.get_cookie("wrpw", '0')
                self.set_cookie("wrpw", str(int(wrn)+1), path = "/", expires_days = 1 )

            self.redirect('%s/topic/%d/%s'% (BASE_URL, pobj.id, pobj.title))
            return

        self.set_header('Content-Type','application/json')
        rspd = {'status': 201, 'msg':'ok'}

        if action == 'readmorecomment':
            fromid = self.get_argument("fromid",'')
            allnum = int(self.get_argument("allnum",0))
            showednum = int(self.get_argument("showednum", EACH_PAGE_COMMENT_NUM))
            if fromid:
                rspd['status'] = 200
                if (allnum - showednum) >= EACH_PAGE_COMMENT_NUM:
                    limit = EACH_PAGE_COMMENT_NUM
                else:
                    limit = allnum - showednum
                cobjs = Comment.get_post_page_comments_by_id( id, fromid, limit )
                rspd['commentstr'] = self.render('comments.html', {'cobjs': cobjs})
                rspd['lavenum'] = allnum - showednum - limit
                self.write(json.dumps(rspd))
            return

        #
        usercomnum = self.get_cookie('usercomnum','0')
        if int(usercomnum) > MAX_COMMENT_NUM_A_DAY:
            rspd = {'status': 403, 'msg':'403: Forbidden'}
            self.write(json.dumps(rspd))
            return

        try:
            timestamp = int(time())
            post_dic = {
                'author': self.get_argument("author"),
                'email': self.get_argument("email",''),
                'content': safe_encode(self.get_argument("con").replace('\r','\n')),
                'url': self.get_argument("url",''),
                'postid': self.get_argument("postid"),
                'add_time': timestamp,
                'toid': self.get_argument("toid",''),
                'visible': COMMENT_DEFAULT_VISIBLE
            }
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 注意必填的三项'
            self.write(json.dumps(rspd))
            return

        pobj = Article.get_article_by_id_simple(id)
        if pobj and not pobj.closecomment:
            cobjid = Comment.add_new_comment(post_dic)
            if cobjid:
                Article.update_post_comment( pobj.comment_num+1, id)
                rspd['status'] = 200
                #rspd['msg'] = '恭喜： 已成功提交评论'

		if GRAVATAR_SUPPORT:
			gravatar = 'http://www.gravatar.com/avatar/%s'%md5(post_dic['email']).hexdigest()
		else:
			gravatar = ''
                rspd['msg'] = self.render('comment.html', {
                        'cobjid': cobjid,
                        'gravatar': gravatar,
                        'url': post_dic['url'],
                        'author': post_dic['author'],
                        'visible': post_dic['visible'],
                        'content': post_dic['content'],
                    })

                clear_cache_by_pathlist(['/','post:%s'%id])
                #send mail
                if not debug:
                    try:
                        if getAttr('NOTICE_MAIL'):
                            tolist = [getAttr('NOTICE_MAIL')]
                        else:
                            tolist = []
                        if post_dic['toid']:
                            tcomment = Comment.get_comment_by_id(toid)
                            if tcomment and tcomment.email:
                                tolist.append(tcomment.email)
                        commenturl = "%s/t/%s#r%s" % (BASE_URL, str(pobj.id), str(cobjid))
                        m_subject = u'有人回复您在 《%s》 里的评论 %s' % ( pobj.title,str(cobjid))
                        m_html = u'这是一封提醒邮件（请勿直接回复）： %s ，请尽快处理： %s' % (m_subject, commenturl)

                        if tolist:
                            import sae.mail
                            sae.mail.send_mail(','.join(tolist), m_subject, m_html,(getAttr('MAIL_SMTP'), int(getAttr('MAIL_PORT')), getAttr('MAIL_FROM'), getAttr('MAIL_PASSWORD'), True))

                    except:
                        pass
            else:
                rspd['msg'] = '错误： 未知错误'
        else:
            rspd['msg'] = '错误： 未知错误'
        self.write(json.dumps(rspd))

class CategoryDetailShort(BaseHandler):
    @client_cache(3600, 'public')
    def get(self, id = ''):
        obj = Category.get_cat_by_id(id)
        if obj:
            self.redirect('%s/category/%s'% (BASE_URL, obj.name), 301)
            return
        else:
            self.redirect(BASE_URL)

class CategoryDetail(BaseHandler):
    @pagecache('cat', PAGE_CACHE_TIME, lambda self,name: name)
    def get(self, name = ''):
        objs = Category.get_cat_page_posts(name, 1)

        catobj = Category.get_cat_by_name(name)
        if catobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        allpost =  catobj.id_num
        allpage = allpost/EACH_PAGE_POST_NUM
        if allpost%EACH_PAGE_POST_NUM:
            allpage += 1

        output = self.render('index.html', {
            'title': "%s - %s"%( catobj.name, getAttr('SITE_TITLE')),
            'keywords':catobj.name,
            'description':getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': allpage,
            'listtype': 'cat',
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
        },layout='_layout.html')
        self.write(output)
        return output

#yobin 20120629 add begin
class ArchiveDetail(BaseHandler):
    #@pagecache('cat', PAGE_CACHE_TIME, lambda self,name: name)
    def get(self, name = ''):
        if not name:
            print 'ArchiveDetail name null'
            name = Archive.get_latest_archive_name()

        objs = Archive.get_archive_page_posts(name, 1)

        archiveobj = Archive.get_archive_by_name(name)
        if archiveobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        allpost =  archiveobj.id_num
        allpage = allpost/EACH_PAGE_POST_NUM
        if allpost%EACH_PAGE_POST_NUM:
            allpage += 1

        output = self.render('index.html', {
            'title': "%s - %s"%( archiveobj.name, getAttr('SITE_TITLE')),
            'keywords':archiveobj.name,
            'description':getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': allpage,
            'listtype': 'archive',
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
        },layout='_layout.html')
        self.write(output)
        return output
#yobin 20120629 add end

class TagDetail(BaseHandler):
    @pagecache()
    def get(self, name = ''):
        objs = Tag.get_tag_page_posts(name, 1)

        catobj = Tag.get_tag_by_name(name)
        if catobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        allpost =  catobj.id_num
        allpage = allpost/EACH_PAGE_POST_NUM
        if allpost%EACH_PAGE_POST_NUM:
            allpage += 1

        output = self.render('index.html', {
            'title': "%s - %s"%( catobj.name, getAttr('SITE_TITLE')),
            'keywords':catobj.name,
            'description':getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': 1,
            'allpage': allpage,
            'listtype': 'tag',
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
        },layout='_layout.html')
        self.write(output)
        return output


class ArticleList(BaseHandler):
    @pagecache('post_list_tag', PAGE_CACHE_TIME, lambda self,listtype,direction,page,name: "%s_%s"%(name,page))
    def get(self, listtype = '', direction = 'next', page = '1', name = ''):
        if listtype == 'cat':
            objs = Category.get_cat_page_posts(name, page)
            catobj = Category.get_cat_by_name(name)
        elif listtype == 'tag':
            objs = Tag.get_tag_page_posts(name, page)
            catobj = Tag.get_tag_by_name(name)
        elif listtype == 'archive':
            objs = Archive.get_archive_page_posts(name, page)
            catobj = Archive.get_archive_by_name(name)
        #
        if catobj:
            pass
        else:
            self.redirect(BASE_URL)
            return

        allpost =  catobj.id_num
        allpage = allpost/EACH_PAGE_POST_NUM
        if allpost%EACH_PAGE_POST_NUM:
            allpage += 1

        output = self.render('index.html', {
            'title': "%s - %s | Part %s"%( catobj.name, getAttr('SITE_TITLE'), page),
            'keywords':catobj.name,
            'description':getAttr('SITE_DECR'),
            'objs': objs,
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_hot_tag_name(),
            'archives': Archive.get_all_archive_name(),
            'page': int(page),
            'allpage': allpage,
            'listtype': listtype,
            'name': name,
            'namemd5': md5(name.encode('utf-8')).hexdigest(),
            'comments': Comment.get_recent_comments(),
            'links':Link.get_all_links(),
            'isauthor':self.isAuthor(),
            'Totalblog':get_count('Totalblog',NUM_SHARDS,0),
        },layout='_layout.html')
        self.write(output)
        return output


class Robots(BaseHandler):
    def get(self):
        self.echo('robots.txt',{'cats':Category.get_all_cat_id()})

class Feed(BaseHandler):
    def get(self):
        posts = Article.get_post_for_homepage()
        output = self.render('index.xml', {
                    'posts':posts,
                    'site_updated':Article.get_last_post_add_time(),
                })
        self.set_header('Content-Type','application/atom+xml')
        self.write(output)

class Sitemap(BaseHandler):
    def get(self, id = ''):
        self.set_header('Content-Type','text/xml')
        self.echo('sitemap.html', {'sitemapstr':Category.get_sitemap_by_id(id), 'id': id})

class Attachment(BaseHandler):
    def get(self, name):
        self.redirect('http://%s-%s.stor.sinaapp.com/%s'% (APP_NAME, STORAGE_DOMAIN_NAME, unquoted_unicode(name)), 301)
        return

#yobin 20131023 for weixin begin
class WxParser(BaseHandler):
    #只是用来做验证的
    def get(self):
        signature = str(self.get_argument('signature',''))
        echostr = str(self.get_argument('echostr',''))
        timestamp = str(self.get_argument('timestamp',''))
        nonce = str(self.get_argument('nonce',''))

        weixin = WeiXin.on_connect(token=WX_TOKEN,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature,
            echostr=echostr)
        if weixin.validate():
            return self.write(echostr)
        return self.write('')

    def post(self):
        body = self.request.body
        weixin = WeiXin.on_message(body)
        mydict = weixin.to_json()

        print "mydict['MsgType'] = %s" % (mydict['MsgType'])

        if mydict['MsgType'] == 'text':
            content = mydict['Content'].encode('utf-8')
            print 'content = %s' % (content)

            help = self.get_help_menu()
            reply = ""

            #TBD 分词这部分需要改造,urllib2不能用？
            if len(content) > 100000:
                _SEGMENT_BASE_URL = 'http://segment.sae.sina.com.cn/urlclient.php'
                payload = urllib.urlencode([('context', content),])
                args = urllib.urlencode([('word_tag', 1), ('encoding', 'UTF-8'),])
                url = _SEGMENT_BASE_URL + '?' + args
                result = urllib2.urlopen(url, payload).read()
                if result:
                    result = eval(result)
                    content = ' '.join(w["word"] for w in result)

            cmd = content[0]
            if cmd == "n":
                rsp = self.wx_get_latest_articles()
                if rsp:
                    reply = weixin.pack_news_xml(mydict,rsp)
            elif cmd == "c":#获取分类列表
                if len(content) == 1:
                    rsp = self.wx_get_categories()
                    if rsp:
                        reply = weixin.pack_text_xml(mydict,rsp)
                else:
                    cid = content[1:]
                    rsp = self.get_category_articles(cid)
                    if rsp:
                        reply = weixin.pack_news_xml(mydict,rsp)
            elif cmd == "l":#列举最新20篇文章条列表
                rsp = self.wx_get_articles()
                if rsp:
                    reply = weixin.pack_text_xml(mydict,rsp)
            elif cmd == "v":# 直接获取某篇文章
                article_id = int(content[1:])
                rsp = self.wx_get_article_by_id(article_id)
                if rsp:
                    reply = weixin.pack_news_xml(mydict,rsp)
            elif cmd == "s":
                #搜索太耗费资源了，而且可能也会有sql注入等安全问题
                #代码只是写写，实际上不会使用
                k = str(content[1:])
                rsp = self.wx_search_article(k)
                if rsp:
                    #reply = weixin.pack_news_xml(mydict,rsp)
                    reply = weixin.pack_news_xml(mydict,"抱歉，此功能暂停使用")
                else:
                    reply = weixin.pack_text_xml(mydict,"抱歉，没有搜到相关关键词")

            if not reply:
                reply = weixin.pack_text_xml(mydict,help)

            self.set_header('Content-Type','application/xml')
            return self.write(reply)

		#以下要后续再拓展了
        elif mydict['MsgType'] == 'image':
            pass
            #wx_handle_pic(mydict['PicUrl'])
        elif mydict['MsgType'] == 'location':
            pass
            #wx_handle_loc(mydict['Location_X'],mydict['Location_Y'],mydict['Scale'],mydict['Label'])
        elif mydict['MsgType'] == 'link':
            pass
            #wx_handle_link(mydict['Title'],mydict['Description'],mydict['Url'])
        elif mydict['MsgType'] == 'event':
            print "mydict['Event'] = %s" % (mydict['Event'])
            if 'subscribe' == mydict['Event']:
                reply = weixin.to_xml(to_user_name=mydict['FromUserName'],
                            from_user_name=mydict['ToUserName'],
                            msg_type='text',
                            content='欢迎欢迎，热烈欢迎。',
                            create_time=str(int(time())),
                            )
                self.set_header('Content-Type','application/xml')
                return self.write(reply)
            elif 'unsubscribe' == mydict['Event']:
                reply = weixin.to_xml(to_user_name=mydict['FromUserName'],
                            from_user_name=mydict['ToUserName'],
                            msg_type='text',
                            content='青山不在，绿水长流，后会有期！',
                            create_time=str(int(time())),
                            )
                self.set_header('Content-Type','application/xml')
                return self.write(reply)
            else:
                pass
            wx_handletext(mydict['Event'],mydict['EventKey'])
        else:
            print "Nootice: mydict['MsgType'] = %s" % (mydict['MsgType'])
        return self.write('')

    #帮助信息
    def get_help_menu(self):
    	help = '''欢迎关注，回复如下按键则可以完成得到相应的回应
    	n : 获取最新文章
    	l ：最新文章列表(article list)
    	v + 数字 ：察看某篇文章 v1938 察看第1938篇文章
    	c : 获得分类列表
    	c + 数字 ： 获取分类文章，如c7 察看读书笔记
        '''
    	return help

    # n for 获取最新的文章
    def wx_get_latest_articles(self):
        posts = Article.get_articles_by_latest()
        articles_msg = {'articles':[]}
        for post in posts:
            slug        = slugfy(post['title'])
            desc        = HTML_REG.sub('',post['content'][:DESCRIPTION_CUT_WORDS])
            shorten_url = '%s/t/%s' % (BASE_URL, post['id'])

            article = {
                       'title': slug,
                       'description':desc,
                       'picUrl':WX_DEFAULT_PIC,
                       'url':shorten_url,
                   }
            # 插入文章
            articles_msg['articles'].append(article)
            article = {}
        return articles_msg

    # 获取文章列表
    def wx_get_articles(self):
        article_list = Article.get_articles_list()
        article_list_str = "最新文章列表供您点阅，回复v+数字即可阅读: \n"
        for i in range(len(article_list)):
            art_id = str(article_list[i].id)
            art_title = article_list[i].title
            art_title = tornado.escape.native_str(art_title)
            art_category = article_list[i].category
            art_category = tornado.escape.native_str(art_category)
            article_list_str +=  art_id + ' ' + art_title + ' ' + art_category + '\n'
        return article_list_str

    #获取目录列表
    def wx_get_categories(self):
        cat_list = Category.get_all_cat_name()
        catstr = "分类列表如下，回复c+分类序号，即可获取该分类文章：\n"
        mylist = ["%d %s" % (int(cat.id),(cat.name).encode('utf-8')) for cat in cat_list]
        mylist.reverse()
        catstr += "\n".join(mylist)
        return catstr

    # 按照分类查找
    def get_category_articles(self, cid):
        article_list = Category.get_cat_page_posts_by_cid(cid)
        if article_list:
            articles_msg = {'articles':[]}
            for obj in article_list:
                slug        = slugfy(obj['title'])
                desc        = HTML_REG.sub('',obj.content[:DESCRIPTION_CUT_WORDS])
                shorten_url = '%s/t/%s' % (BASE_URL, obj['id'])
                article = {
                        'title': slug,
                        'description':desc,
                        'picUrl':WX_DEFAULT_PIC,
                        'url':shorten_url,
                    }
                articles_msg['articles'].append(article)
                article = {}
            return articles_msg
        return ''

    #根据关键词搜索文章，此函数用不到了
    def wx_search_article(self, k):
        article = Article.get_article_by_keyword(k)
        if article:
            title = article.slug
            description = article.description
            picUrl = WX_DEFAULT_PIC
            url = article.absolute_url
            count = 1
            articles_msg = {'articles':[]}
            for i in range(0,count):
                article = {
                        'title':title,
                        'description':description,
                        'picUrl':picUrl,
                        'url':url
                    }
                articles_msg['articles'].append(article)
                article = {}
            return articles_msg
        return ''

    def wx_get_article_by_id(self, post_id):
        article = Article.get_article_by_id_detail(post_id)
        if article:
            title = article.slug
            description = article.description
            picUrl = WX_DEFAULT_PIC
            url = article.absolute_url
            count = 1

            articles_msg = {'articles':[]}
            for i in range(0,count):
                article = {
                        'title':title,
                        'description':description,
                        'picUrl':picUrl,
                        'url':url
                    }
                articles_msg['articles'].append(article)
                article = {}
            return articles_msg
        return ''
#yobin 20131023 for weixin end

########
urls = [
    (r"/", HomePage),
    (r"/robots.txt", Robots),
    (r"/feed", Feed),
    (r"/index.xml", Feed),
    (r"/t/(\d+)$", PostDetailShort),
    (r"/topic/(\d+)/(.*)$", PostDetail),
    (r"/index_(prev|next)_page/(\d+)/(\d+)/$", IndexPage),
    (r"/c/(\d+)$", CategoryDetailShort),
    (r"/category/(.+)/$", CategoryDetail),
    (r"/tag/(.+)/$", TagDetail),
    (r"/archive/", ArchiveDetail),
    (r"/archive/(.+)/$", ArchiveDetail),
    (r"/(cat|tag|archive)_(prev|next)_page/(\d+)/(.+)/$", ArticleList),
    (r"/sitemap_(\d+)\.xml$", Sitemap),
    (r"/attachment/(.+)$", Attachment),
    (r"/wx",WxParser),
]

