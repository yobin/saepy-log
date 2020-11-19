# -*- coding: utf-8 -*-

import logging
import re

try:
    import json
except:
    import simplejson as json

from hashlib import md5
from time import time
from datetime import datetime,timedelta
from urllib import urlencode

from common import *

from setting import *
from model import Article, Comment, Link, Category, Tag, User, MyData, Archive

import markdown2 as markdown
from plugins import parse_text

if not debug:
    import sae.mail
    from sae.taskqueue import add_task
    import sae.storage
    from sae.storage import Bucket

######
def put_obj2storage(file_name = '', data = '', expires='365', type=None, encoding= None, domain_name = STORAGE_DOMAIN_NAME):
    whichStorage = int(getAttr('DEFAULT_STORAGE'))
    if whichStorage == 0:
        bucket = Bucket(domain_name)
        bucket.put_object(file_name, data, content_type=type, content_encoding= encoding)
        return bucket.generate_url(file_name)
    elif whichStorage == 1:
        import qiniu.conf,qiniu.rs,qiniu.io
        qiniu.conf.ACCESS_KEY = getAttr('QNKEY')
        qiniu.conf.SECRET_KEY = getAttr('QNSECRET')
        policy = qiniu.rs.PutPolicy(getAttr('QNSTORAGE'))
        uptoken = policy.token()
        key = file_name
        if key[0] == "/":
            key = key[1:]
        ret, err = qiniu.io.put(uptoken, key, data)
        if err is not None:
            print 'err = ', err
            return ''
        ###下面返回的网址有可能不同，有的是 xxxx.u.qiniudn.com 请改为自己的
        return "http://%s/%s" % (getAttr('QNDOMAIN'), key)
    else:
        #可后续扩展其他云存储
        pass
    return ''

######
class HomePage(BaseHandler):
    @authorized()
    def get(self):
        output = self.render('admin_index.html', {
            'title': "%s - %s"%(getAttr('SITE_TITLE'),getAttr('SITE_SUB_TITLE')),
            'keywords':getAttr('KEYWORDS'),
            'description':getAttr('SITE_DECR'),
            'test': '',
        },layout='_layout_admin.html')
        self.write(output)
        return output

class Login(BaseHandler):
    def get(self):
        self.echo('admin_login.html', {
            'title': "管理员登录",
            'has_user': User.check_has_user()
        },layout='_layout_admin.html')

    def post(self):
        try:
            name = self.get_argument("name")
            password = self.get_argument("password")
        except:
            self.redirect('%s/admin/login'% BASE_URL)
            return

        if name and password:
            has_user = User.check_has_user()
            if has_user:
                #check user
                password = md5(password.encode('utf-8')).hexdigest()
                user = User.check_user( name, password)
                if user:
                    #logging.error('user ok')
                    self.set_cookie('username', name, path="/", expires_days = 365 )
                    self.set_cookie('userpw', password, path="/", expires_days = 365 )
                    self.redirect('%s/admin/'% BASE_URL)
                    return
                else:
                    #logging.error('user not ok')
                    self.redirect('%s/admin/login'% BASE_URL)
                    return
            else:
                #add new user
                newuser = User.add_new_user( name, password)
                if newuser:
                    self.set_cookie('username', name, path="/", expires_days = 365 )
                    self.set_cookie('userpw', md5(password.encode('utf-8')).hexdigest(), path="/", expires_days = 365 )
                    self.redirect('%s/admin/'% BASE_URL)
                    return
                else:
                    self.redirect('%s/admin/login'% BASE_URL)
                    return
        else:
            self.redirect('%s/admin/login'% BASE_URL)

class Logout(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('%s/admin/login'% BASE_URL)

class AddUser(BaseHandler):
    @authorized()
    def get(self):
        pass

class Forbidden(BaseHandler):
    def get(self):
        self.write('Forbidden page')

class FileUpload(BaseHandler):
    @authorized()
    def post(self):
        self.set_header('Content-Type','text/html')
        rspd = {'status': 201, 'msg':'ok'}

        filetoupload = self.request.files['filetoupload']
        if filetoupload:
            myfile = filetoupload[0]
            try:
                file_type = myfile['filename'].split('.')[-1].lower()
                new_file_name = "%s.%s"% (str(int(time())), file_type)
            except:
                file_type = ''
                new_file_name = str(int(time()))
            ##
            mime_type = myfile['content_type']
            encoding = None
            ###

            try:
                attachment_url = put_obj2storage(file_name = str(new_file_name), data = myfile['body'], expires='365', type= mime_type, encoding= encoding)
            except:
                attachment_url = ''

            if attachment_url:
                rspd['status'] = 200
                rspd['filename'] = myfile['filename']
                rspd['msg'] = attachment_url
            else:
                rspd['status'] = 500
                rspd['msg'] = 'put_obj2storage erro, try it again.'
        else:
            rspd['msg'] = 'No file uploaded'
        self.write(json.dumps(rspd))
        return

class PostPrevewPage(BaseHandler):
    @authorized()
    def get(self):
        self.write("This is a preview page.")

    @authorized()
    def post(self):
        data = self.get_argument("data", "no post data")
        if data:
            data = markdown.markdown(parse_text(data))
        self.echo("admin_preview.html", {"title":"Post preview", "data": data})

class AddPost(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_addpost.html', {
            'title': "添加文章",
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_all_tag_name(),
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        self.set_header('Content-Type','application/json')
        rspd = {'status': 201, 'msg':'ok'}

        try:
            tf = {'true':1,'false':0}
            timestamp = int(time())
            content = self.get_argument("con")
            if getAttr('MARKDOWN'):
                #content = markdown.markdown(parse_text(content))
                content = content.encode("utf-8")
            post_dic = {
                'category': self.get_argument("cat"),
                'title': self.get_argument("tit"),
                'content': content,
                'tags': self.get_argument("tag",'').replace(u'，',','),
                'closecomment': self.get_argument("clo",'0'),
                'password': self.get_argument("password",''),
                'add_time': timestamp,
                'edit_time': timestamp,
                'archive': genArchive(),
            }
            if MYSQL_TO_KVDB_SUPPORT:
                post_dic['comment_num'] = '0'

            if post_dic['tags']:
                tagslist = set([x.strip() for x in post_dic['tags'].split(',')])
                try:
                    tagslist.remove('')
                except:
                    pass
                if tagslist:
                    post_dic['tags'] = ','.join(tagslist)
            post_dic['closecomment'] = tf[post_dic['closecomment'].lower()]
        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 注意必填的三项'
            self.write(json.dumps(rspd))
            return

        postid = Article.add_new_article(post_dic)
        if postid:
            keyname = 'pv_%s' % (str(postid))
            set_count(keyname,0,0)

            Category.add_postid_to_cat(post_dic['category'], str(postid))
            Archive.add_postid_to_archive(genArchive(), str(postid))
            increment('Totalblog')
            if post_dic['tags']:
                Tag.add_postid_to_tags(post_dic['tags'].split(','), str(postid))

            rspd['status'] = 200
            rspd['msg'] = '完成： 你已经成功添加了一篇文章 <a href="/t/%s" target="_blank">查看</a>' % str(postid)
            #clear_cache_by_pathlist(['/', 'cat:%s' % quoted_string(post_dic['category']), 'post_list_index',])
            clear_all_cache()#yobin 20160921

            if not debug:
                add_task('default', '/task/pingrpctask')

            self.write(json.dumps(rspd))
            return
        else:
            rspd['status'] = 500
            rspd['msg'] = '错误： 未知错误，请尝试重新提交'
            self.write(json.dumps(rspd))
            return

class EditPost(BaseHandler):
    @authorized()
    def get(self, id = ''):
        obj = None
        if id:
            obj = Article.get_article_by_id_edit(id)
        self.echo('admin_editpost.html', {
            'title': "编辑文章",
            'cats': Category.get_all_cat_name(),
            'tags': Tag.get_all_tag_name(),
            'obj': obj
        },layout='_layout_admin.html')

    @authorized()
    def post(self, id = ''):
        act = self.get_argument("act",'')
        if act == 'findid':
            eid = self.get_argument("id",'')
            self.redirect('%s/admin/edit_post/%s'% (BASE_URL, eid))
            return

        self.set_header('Content-Type','application/json')
        rspd = {'status': 201, 'msg':'ok'}
        oldobj = Article.get_article_by_id_edit(id)

        content = self.get_argument("con")
        if getAttr('MARKDOWN'):
            #content = markdown.markdown(parse_text(content))
            content = content.encode("utf-8")

        try:
            tf = {'true':1,'false':0}
            timestamp = int(time())
            post_dic = {
                'category': self.get_argument("cat"),
                'title': self.get_argument("tit"),
                'content': content,
                'tags': self.get_argument("tag",'').replace(u'，',',').encode('utf-8'),
                'closecomment': self.get_argument("clo",'false'),
                'password': self.get_argument("password",''),
                'edit_time': timestamp,
                'id': id
            }

            if MYSQL_TO_KVDB_SUPPORT:
                post_dic['add_time'] = oldobj['add_time']
                post_dic['archive'] = oldobj['archive']
                post_dic['comment_num'] = oldobj['comment_num']

            if post_dic['tags']:
                tagslist = set([x.strip() for x in post_dic['tags'].split(',')])
                try:
                    tagslist.remove('')
                except:
                    pass
                if tagslist:
                    post_dic['tags'] = ','.join(tagslist)
            post_dic['closecomment'] = tf[post_dic['closecomment'].lower()]

        except:
            rspd['status'] = 500
            rspd['msg'] = '错误： 注意必填的三项'
            self.write(json.dumps(rspd))
            return

        postid = Article.update_post_edit(post_dic)
        if postid:
            if MYSQL_TO_KVDB_SUPPORT:
                oldobj_category = oldobj['category']
                oldobj_tags     = oldobj['tags']
            else:
                oldobj_category = oldobj.category
                oldobj_tags     = oldobj.tags
            cache_key_list = ['/', 'post:%s'% id, 'cat:%s' % quoted_string(oldobj_category)]
            if oldobj_category != post_dic['category']:
                #cat changed
                Category.add_postid_to_cat(post_dic['category'], str(postid))
                Category.remove_postid_from_cat(oldobj_category, str(postid))
                cache_key_list.append('cat:%s' % quoted_string(post_dic['category']))

            if oldobj_tags != post_dic['tags']:
                #tag changed
                old_tags = set(oldobj_tags.split(','))
                new_tags = set(post_dic['tags'].split(','))

                removed_tags = old_tags - new_tags
                added_tags = new_tags - old_tags

                if added_tags:
                    Tag.add_postid_to_tags(added_tags, str(postid))

                if removed_tags:
                    Tag.remove_postid_from_tags(removed_tags, str(postid))

            clear_cache_by_pathlist(cache_key_list)
            rspd['status'] = 200
            rspd['msg'] = '完成： 你已经成功编辑了一篇文章 <a href="/t/%s" target="_blank">查看编辑后的文章</a>' % str(postid)
            self.write(json.dumps(rspd))
            return
        else:
            rspd['status'] = 500
            rspd['msg'] = '错误： 未知错误，请尝试重新提交'
            self.write(json.dumps(rspd))
            return

class DelPost(BaseHandler):
    @authorized()
    def get(self, id = ''):
        #try:
        if id:
            oldobj = Article.get_article_by_id_edit(id)
            print 'DelPost()',oldobj
            if not oldobj:
                return
            if MYSQL_TO_KVDB_SUPPORT:
                oldobj_category = oldobj['category']
                oldobj_archive = oldobj['archive']
                oldobj_tags = oldobj['tags']
            else:
                oldobj_category = oldobj.category
                oldobj_archive = oldobj.archive
                oldobj_tags    = oldobj.tags

            Category.remove_postid_from_cat(oldobj_category, str(id))
            Archive.remove_postid_from_archive(oldobj_archive, str(id))
            Tag.remove_postid_from_tags( set(oldobj_tags.split(','))  , str(id))
            Article.del_post_by_id(id)
            increment('Totalblog',NUM_SHARDS,-1)
            cache_key_list = ['/', 'post:%s'% id, 'cat:%s' % quoted_string(oldobj_category)]
            clear_cache_by_pathlist(cache_key_list)
            clear_cache_by_pathlist(['post:%s'%id])
            self.redirect('%s/admin/edit_post/'% (BASE_URL))
        #except:
        #    pass

class EditComment(BaseHandler):
    @authorized()
    def get(self, id = ''):
        obj = None
        if id:
            obj = Comment.get_comment_by_id(id)
            if obj:
                act = self.get_argument("act",'')
                if act == 'del':
                    Comment.del_comment_by_id(id)
                    if MYSQL_TO_KVDB_SUPPORT:
                        clear_cache_by_pathlist(['post:%d' % int(obj['postid'])])
                    else:
                        clear_cache_by_pathlist(['post:%d' % int(obj.postid)])
                    self.redirect('%s/admin/comment/'% (BASE_URL))
                    return
        self.echo('admin_comment.html', {
            'title': "管理评论",
            'obj': obj,
            'comments': Comment.get_recent_comments(ADMIN_RECENT_COMMENT_NUM),
        },layout='_layout_admin.html')

    @authorized()
    def post(self, id = ''):
        act = self.get_argument("act",'')
        if act == 'findid':
            eid = self.get_argument("id",'')
            self.redirect('%s/admin/comment/%s'% (BASE_URL, eid))
            return

        tf = {'true':1,'false':0}
        post_dic = {
            'author': self.get_argument("author"),
            'email': self.get_argument("email",''),
            'content': safe_encode(self.get_argument("content").replace('\r','\n')),
            'url': self.get_argument("url",''),
            'visible': self.get_argument("visible",'false'),
            'id': id
        }
        post_dic['visible'] = tf[post_dic['visible'].lower()]

        if MYSQL_TO_KVDB_SUPPORT:
            obj = Comment.get_comment_by_id(id)
            for k,v in obj.items():
                if k not in post_dic:
                    post_dic[k] = v

        Comment.update_comment_edit(post_dic)
        clear_cache_by_pathlist(['post:%s'%id])
        self.redirect('%s/admin/comment/%s'% (BASE_URL, id))
        return

class LinkBroll(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act",'')
        id = self.get_argument("id",'')

        obj = None
        if act == 'del':
            if id:
                Link.del_link_by_id(id)
                clear_cache_by_pathlist(['/'])
            self.redirect('%s/admin/links'% (BASE_URL))
            return
        elif act == 'edit':
            if id:
                obj = Link.get_link_by_id(id)
                clear_cache_by_pathlist(['/'])
        self.echo('admin_link.html', {
            'title': "管理友情链接",
            'objs': Link.get_all_links(),
            'obj': obj,
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        act = self.get_argument("act",'')
        id = self.get_argument("id",'')
        name = self.get_argument("name",'')
        sort = self.get_argument("sort",'0')
        url = self.get_argument("url",'')

        if name and url:
            params = {'id': id, 'name': name, 'url': url, 'displayorder': sort}
            if act == 'add':
                Link.add_new_link(params)

            if act == 'edit':
                Link.update_link_edit(params)

            clear_cache_by_pathlist(['/'])

        self.redirect('%s/admin/links'% (BASE_URL))
        return

class BlogSetting(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting.html', {
            'title': "基本设置",
            'sitetitle': getAttr('SITE_TITLE'),
            'sitetitle2': getAttr('SITE_TITLE2'),
            'sitesubtitle':getAttr('SITE_SUB_TITLE'),
            'keywords':getAttr('KEYWORDS'),
            'sidedecr':getAttr('SITE_DECR'),
            'adminname':getAttr('ADMIN_NAME'),
            'notice':getAttr('NOTICE_MAIL'),
            'mailfrom':getAttr('MAIL_FROM'),
            'psw':getAttr('MAIL_PASSWORD'),
            'mailsmtp':getAttr('MAIL_SMTP'),
            'port':getAttr('MAIL_PORT'),
            'move_secret':getAttr('MOVE_SECRET'),
            'markdown':getAttr('MARKDOWN'),
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        value = self.get_argument("sitetitle",'')
        if value:
            setAttr('SITE_TITLE',value)

        value = self.get_argument("sitetitle2",'')
        if value:
            setAttr('SITE_TITLE2',value)

        value = self.get_argument("sitesubtitle",'')
        if value:
            setAttr('SITE_SUB_TITLE',value)

        value = self.get_argument("keywords",'')
        if value:
            setAttr('KEYWORDS',value)

        value = self.get_argument("sidedecr",'')
        if value:
            setAttr('SITE_DECR',value)

        value = self.get_argument("adminname",'')
        if value:
            setAttr('ADMIN_NAME',value)

        value = self.get_argument("move_secret",'')
        if value:
            setAttr('MOVE_SECRET',value)

        value = self.get_argument("notice",'')
        if value:
            setAttr('NOTICE_MAIL',value)

        value = self.get_argument("mailfrom",'')
        if value:
            setAttr('MAIL_FROM',value)

        value = self.get_argument("psw",'')
        if value:
            setAttr('MAIL_PASSWORD',value)

        value = self.get_argument("mailsmtp",'')
        if value:
            setAttr('MAIL_SMTP',value)

        value = self.get_argument("port",'')
        if value:
            setAttr('MAIL_PORT',value)

        value = self.get_argument("markdown",'')
        setAttr('MARKDOWN',value)

        clear_cache_by_pathlist(['/'])

        self.redirect('%s/admin/setting'% (BASE_URL))
        return

class BlogSetting2(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting.html', {
            'title': "详细设置",
            'sitetitle': getAttr('SITE_TITLE'),
            'sitesubtitle':getAttr('SITE_SUB_TITLE'),
            'keywords':getAttr('KEYWORDS'),
            'sidedecr':getAttr('SITE_DECR'),
            'adminname':getAttr('ADMIN_NAME'),
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        sitetitle = self.get_argument("sitetitle",'')
        if sitetitle:
            setAttr('SITE_TITLE',sitetitle)

        clear_cache_by_pathlist(['/'])

        self.redirect('%s/admin/setting2'% (BASE_URL))
        return


class BlogSetting3(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_setting3.html', {
            'title': "广告设置",
            'ANALYTICS_CODE':getAttr('ANALYTICS_CODE'),
            'ADSENSE_CODE1':getAttr('ADSENSE_CODE1'),
            'ADSENSE_CODE2':getAttr('ADSENSE_CODE2'),
            'ADSENSE_CODE3':getAttr('ADSENSE_CODE3'),
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        ANALYTICS_CODE = self.get_argument("ANALYTICS_CODE",'')
        setAttr('ANALYTICS_CODE',ANALYTICS_CODE)

        ADSENSE_CODE1 = self.get_argument("ADSENSE_CODE1",'')
        setAttr('ADSENSE_CODE1',ADSENSE_CODE1)

        ADSENSE_CODE2 = self.get_argument("ADSENSE_CODE2",'')
        setAttr('ADSENSE_CODE2',ADSENSE_CODE2)

        ADSENSE_CODE3 = self.get_argument("ADSENSE_CODE3",'')
        setAttr('ADSENSE_CODE3',ADSENSE_CODE3)
        clear_cache_by_pathlist(['/'])

        self.redirect('%s/admin/setting3'% (BASE_URL))
        return

class StorageSetting(BaseHandler):
    @authorized()
    def get(self):
        if not getAttr('DEFAULT_STORAGE'):
            setAttr('DEFAULT_STORAGE',0)

        if not getAttr('SAESTORAGE'):
            setAttr('SAESTORAGE','')

        if not getAttr('QNKEY'):
            setAttr('QNKEY','')

        if not getAttr('QNSECRET'):
            setAttr('QNSECRET','')

        if not getAttr('QNSTORAGE'):
            setAttr('QNSTORAGE',STORAGE_DOMAIN_NAME)

        if not getAttr('QNDOMAIN'):
            setAttr('QNDOMAIN','')

        self.echo('admin_storage.html', {
            'title': "存储设置",
            'defaultstorage':getAttr('DEFAULT_STORAGE'),
            'saestorage':getAttr('SAESTORAGE'),
            'qnkey':getAttr('QNKEY'),
            'qnsecret':getAttr('QNSECRET'),
            'qnstorage':getAttr('QNSTORAGE'),
            'qndomain':getAttr('QNDOMAIN'),
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        DEFAULT_STORAGE = self.get_argument("defaultstorage",0)
        setAttr('DEFAULT_STORAGE',int(DEFAULT_STORAGE))

        SAESTORAGE = self.get_argument("saestorage",'')
        setAttr('SAESTORAGE',SAESTORAGE)

        QNKEY = self.get_argument("qnkey",'')
        setAttr('QNKEY',QNKEY)

        QNSECRET = self.get_argument("qnsecret",'')
        setAttr('QNSECRET',QNSECRET)

        QNSTORAGE = self.get_argument("qnstorage",'')
        setAttr('QNSTORAGE',QNSTORAGE)

        QNDOMAIN = self.get_argument("qndomain",'')
        setAttr('QNDOMAIN',QNDOMAIN)

        #clear_cache_by_pathlist(['/'])

        self.redirect('%s/admin/storage'% (BASE_URL))
        return

class KVDBAdmin(BaseHandler):
    @authorized()
    def get(self):
        self.echo('admin_kvdb.html', {
            'title': "KVDB面板",
            'key': '',
            'obj': '',
        },layout='_layout_admin.html')

    @authorized()
    def post(self):
        key = self.get_argument("key",'')
        self.echo('admin_kvdb.html', {
            'title': "KVDB面板",
            'key': key,
            'obj': decode_special_txt(getkv(key)),
        },layout='_layout_admin.html')

class KVDBSave(BaseHandler):
    @authorized()
    def post(self):
        k = self.get_argument("key",'')
        v = self.get_argument("content",'')
        if k and v:
            setkv(k,encode_special_txt(v))
        self.redirect('%s/admin/kvdb'% (BASE_URL))

class KVDBDel(BaseHandler):
    @authorized()
    def post(self):
        k = self.get_argument("key",'')
        if k :
            delkv(k)
        self.redirect('%s/admin/kvdb'% (BASE_URL))

class KVDBDownload(BaseHandler):
    @authorized()
    def post(self):
        import cStringIO as StringIO
        import gzip

        k = self.get_argument("key",'')
        if k :
            filename = 'kvdb_%s.zip' % (k)
            self.set_header('Content-Type','application/zip')
            self.set_header('Content-Disposition',"attachment;filename=%s;charset=utf-8" % filename)

            buf = StringIO.StringIO()
            f=gzip.GzipFile(mode="w", fileobj=buf)
            f.write(decode_special_txt(getkv(k).encode('utf-8')))
            f.close()
            return self.write(buf.getvalue())

class FlushData(BaseHandler):
    @authorized()
    def get(self):
        act = self.get_argument("act",'')
        if act == 'flush':
            MyData.flush_all_data()
            clear_all_cache()
            clearAllKVDB()
            self.redirect('/admin/flushdata')
            return
        elif act == 'flushcache':
            clear_all_cache()
            self.redirect('/admin/flushdata')
            return

        self.echo('admin_flushdata.html', {
            'title': "清空缓存/数据",
        },layout='_layout_admin.html')

class PingRPCTask(BaseHandler):
    def get(self):
        for n in range(len(XML_RPC_ENDPOINTS)):
            add_task('default', '%s/task/pingrpc/%d' % (BASE_URL, n))
        self.write(str(time()))

    post = get

class PingRPC(BaseHandler):
    def get(self, n = 0):
        import urllib2

        pingstr = self.render('rpc.xml', {'article_id':Article.get_max_id()})

        headers = {
            'User-Agent':'request',
            'Content-Type' : 'text/xml',
            'Content-length' : str(len(pingstr))
        }

        req = urllib2.Request(
            url = XML_RPC_ENDPOINTS[int(n)],
            headers = headers,
            data = pingstr,
        )
        try:
            content = urllib2.urlopen(req).read()
            tip = 'Ping ok' + content
        except:
            tip = 'ping erro'

        self.write(str(time()) + ": " + tip)
        #add_task('default', '%s/task/sendmail'%BASE_URL, urlencode({'subject': tip, 'content': tip + " " + str(n)}))

    post = get

class SendMail(BaseHandler):
    def post(self):
        subject = self.get_argument("subject",'')
        content = self.get_argument("content",'')

        if subject and content:
            sae.mail.send_mail(getAttr('NOTICE_MAIL'), subject, content,(getAttr('MAIL_SMTP'), int(getAttr('MAIL_PORT')), getAttr('MAIL_FROM'), getAttr('MAIL_PASSWORD'), True))
#初始化一些参数
def Init():
    if not getAttr('MAIL_SMTP'):
        setAttr('MAIL_SMTP','smtp.gmail.com')
    if not getAttr('MAIL_PORT'):
        setAttr('MAIL_PORT',587)
    if not getAttr('EACH_PAGE_POST_NUM'):
        setAttr('EACH_PAGE_POST_NUM',10)
    if not getAttr('EACH_PAGE_COMMENT_NUM'):
        setAttr('EACH_PAGE_COMMENT_NUM',10)
    if not getAttr('RELATIVE_POST_NUM'):
        setAttr('RELATIVE_POST_NUM',5)
    if not getAttr('SHORTEN_CONTENT_WORDS'):
        setAttr('SHORTEN_CONTENT_WORDS',150)
    if not getAttr('DESCRIPTION_CUT_WORDS'):
        setAttr('DESCRIPTION_CUT_WORDS',100)
    if not getAttr('RECENT_COMMENT_NUM'):
        setAttr('RECENT_COMMENT_NUM',5)
    if not getAttr('RECENT_COMMENT_CUT_WORDS'):
        setAttr('RECENT_COMMENT_CUT_WORDS',20)
    if not getAttr('LINK_NUM'):
        setAttr('LINK_NUM',10)
    if not getAttr('MAX_COMMENT_NUM_A_DAY'):
        setAttr('MAX_COMMENT_NUM_A_DAY',10)
    if not getAttr('PAGE_CACHE_TIME'):
        setAttr('PAGE_CACHE_TIME',3600*24)
    if not getAttr('POST_CACHE_TIME'):
        setAttr('POST_CACHE_TIME',3600*24)
    if not getAttr('HOT_TAGS_NUM'):
        setAttr('HOT_TAGS_NUM',30)
    if not getAttr('MAX_ARCHIVES_NUM'):
        setAttr('MAX_ARCHIVES_NUM',50)
    if not getAttr('MAX_IDLE_TIME'):
        setAttr('MAX_IDLE_TIME',5)
    if not getAttr('HOT_TAGS_NUM'):
        setAttr('HOT_TAGS_NUM',30)
    if not getAttr('MOVE_SECRET'):
        setAttr('MOVE_SECRET','123456')
    if not getAttr('MARKDOWN'):
        setAttr('MARKDOWN','')

class Install(BaseHandler):
    def get(self):
        try:
            self.write('如果出现错误请尝试刷新本页。<br>')
            has_user = User.check_has_user()
            if has_user:
                self.write('博客已经成功安装了，你可以直接 <a href="/admin/flushdata">清空网站数据</a>')
            else:
                self.write('博客数据库已经建立，现在就去 <a href="/admin/">设置一个管理员帐号</a>')
            Init()
        except:
            try:
                MyData.creat_table()
            except:
                pass
            self.write('博客已经成功安装了，现在就去 <a href="/admin/">设置一个管理员帐号</a>')

class NotFoundPage(BaseHandler):
    def get(self):
        self.set_status(404)
        self.echo('error.html', {
            'page': '404',
            'title': "Can't find out this URL",
            'h2': 'Oh, my god!',
            'msg': 'Something seems to be lost...'
        })

#迁移博客
class MovePost(BaseHandler):
    def post(self):
        self.set_header('Content-Type','application/json')
        rspd = {'status': 201, 'msg':'ok'}

        secret = self.get_argument("s","")

        if secret <> getAttr('MOVE_SECRET'):
            user = False
            rspd['status'] = 403
            rspd['msg'] = 'secret code err.'
            self.write(json.dumps(rspd))
            return

        try:
            tf = {'true':1,'false':0}
            timestamp = int(time())
            #print timestamp
            post_dic = {
                'category': self.get_argument("cat"),
                'title': self.get_argument("tit"),
                'content': self.get_argument("con"),
                'tags': self.get_argument("tag",'').replace(u'，',','),
                'closecomment': self.get_argument("clo",'false'),
                'password': self.get_argument("p",''),
                'add_time': self.get_argument("addtime",timestamp),
                'edit_time': self.get_argument("edit_time",timestamp),
                'archive': self.get_argument("archive",genArchive()),
                'pv': int(self.get_argument("pv",0)),
            }
            if post_dic['tags']:
                tagslist = set([x.strip() for x in post_dic['tags'].split(',')])
                try:
                    tagslist.remove('')
                except:
                    pass
                if tagslist:
                    post_dic['tags'] = ','.join(tagslist)
            print '====================='
            print post_dic['pv']
            post_dic['closecomment'] = tf[post_dic['closecomment'].lower()]
        except:
            rspd['status'] = 500
            rspd['msg'] = 'Para err.'
            self.write(json.dumps(rspd))
            return

        postid = Article.add_new_article(post_dic)
        if postid:
            Category.add_postid_to_cat(post_dic['category'], str(postid))
            Archive.add_postid_to_archive(post_dic['archive'], str(postid))
            keyname = 'pv_%s' % (str(postid))
            set_count(keyname,0,post_dic['pv'])
            increment('Totalblog')
            if post_dic['tags']:
                Tag.add_postid_to_tags(post_dic['tags'].split(','), str(postid))

            rspd['status'] = 200
            #rspd['msg'] = '完成： 你已经成功添加了一篇文章 <a href="/t/%s" target="_blank">查看</a>' % str(postid)
            #clear_cache_by_pathlist(['/', 'cat:%s' % quoted_string(post_dic['category'])])

            #if not debug:
            #    #add_task('default', '/task/pingrpctask')

            self.write(json.dumps(rspd))
            return
        else:
            rspd['status'] = 500
            rspd['msg'] = 'Unknown err.'
            self.write(json.dumps(rspd))
            return

#MYSQL_TO_KVDB_SUPPORT
class SetArches(BaseHandler):
    def post(self, secret = ''):
        arches = self.get_argument("arches",''),
        if arches and secret:
            if secret == getAttr('MOVE_SECRET'):
                Archive.set_arches(encode_special_txt(arches[0]))
                return self.write('1')
        return self.write('0')

class SetTags(BaseHandler):
    def post(self, secret = ''):
        tags = self.get_argument("tags",''),
        if tags and secret:
            if secret == getAttr('MOVE_SECRET'):
                Tag.set_tags(encode_special_txt(tags[0]))
                return self.write('1')
        return self.write('0')

class SetCats(BaseHandler):
    def post(self, secret = ''):
        cats = self.get_argument("cats",''),
        if cats and secret:
            if secret == getAttr('MOVE_SECRET'):
                Category.set_cats(encode_special_txt(cats[0]))
                return self.write('1')
        return self.write('0')

class SetComment(BaseHandler):
    def post(self, secret = '', id = ''):
        comment = self.get_argument("comment",''),
        if id and comment and secret:
            if secret == getAttr('MOVE_SECRET'):
                Comment.set_comm(id,encode_special_txt(comment[0]))
                return self.write('1')
        return self.write('Fail')

class SetComments(BaseHandler):
    def post(self, secret = ''):
        comments = self.get_argument("comments",''),
        if comments and secret:
            if secret == getAttr('MOVE_SECRET'):
                Comment.set_comms(comments[0])
                return self.write('1')
        return self.write('Fail')

class SetPcomm(BaseHandler):
    def post(self, secret = ''):
        pcomm = self.get_argument("pcomm",''),
        if pcomm and secret:
            if secret == getAttr('MOVE_SECRET'):
                Comment.set_pcomm(encode_special_txt(pcomm[0]))
                return self.write('1')
        return self.write('Fail')

class SetArticle(BaseHandler):
    def post(self, secret = '', id = ''):
        article = self.get_argument("article",''),
        if id and article and secret:
            if secret == getAttr('MOVE_SECRET'):
                Article.set_article(id,encode_special_txt(article[0]))
                return self.write('1')
        return self.write('Fail')

class SetArticles(BaseHandler):
    def post(self, secret = ''):
        articles = self.get_argument("articles",''),
        if articles and secret:
            if secret == getAttr('MOVE_SECRET'):
                Article.set_articles(articles[0])
                return self.write('1')
        return self.write('Fail')

class SetUser(BaseHandler):
    def post(self, secret = ''):
        data = self.get_argument("data",''),
        if id and data and secret:
            if secret == getAttr('MOVE_SECRET'):
                User.set_user(encode_special_txt(data[0]))
                return self.write('1')
        return self.write('Fail')

class SetLink(BaseHandler):
    def post(self, secret = ''):
        data = self.get_argument("data",''),
        if id and data and secret:
            if secret == getAttr('MOVE_SECRET'):
                Link.set_link(encode_special_txt(data[0]))
                return self.write('1')
        return self.write('Fail')

#yobin add kvdb panel 20160824 begin
class kvpanel_index(BaseHandler):
    @authorized()
    def get(self):
        kv = sae.kvdb.KVClient()
        path = self.request.path
        prefix = self.get_argument('prefix','')
        limit = self.get_argument('limit',20)
        prev_marker = self.get_argument('prev_marker','')
        marker = str(self.get_argument('marker',''))

        results = list(kv.get_by_prefix(str(prefix),limit=int(limit),marker=marker))
        if results and len(results):
            marker  = results[-1][0]

        mdict = {'results':results,
            'prefix':prefix,
            'prev_marker':prev_marker,
            'marker':marker,
            'path':path,
            'limit':limit}
        return self.echo('kvdbpannel.html',mdict)

class kvpanel_set(BaseHandler):
    @authorized()
    def post(self):
        key = self.get_argument('key','')
        val = self.get_argument('val','')
        if key and val:
            kv = sae.kvdb.KVClient()
            kv.set(str(key),encode_special_txt(str(val)))
        return self.redirect('/kvdbpanel/kv/')

class kvpanel_del(BaseHandler):
    @authorized()
    def post(self):
        key = self.get_argument('key','')
        if key:
            kv = sae.kvdb.KVClient()
            kv.delete(str(key))
        return self.redirect('/kvdbpanel/kv/')

class kvpanel_get(BaseHandler):
    @authorized()
    def get(self):
        key = self.get_argument('key','')
        ans = ''
        if key:
            kv = sae.kvdb.KVClient()
            ans = decode_special_txt(str(kv.get(str(key))))
        return self.redirect('/kvdbpanel/kv/')
#yobin add kvdb panel 20160824 end
#####
if MYSQL_TO_KVDB_SUPPORT:
    urls = [
    (r"/admin/kv/setarches/(.*?)/", SetArches),
    (r"/admin/kv/settags/(.*?)/", SetTags),
    (r"/admin/kv/setcats/(.*?)/", SetCats),
    (r"/admin/kv/setpcomm/(.*?)/", SetPcomm),
    (r"/admin/kv/setcomments/(.*?)/", SetComments),
    (r"/admin/kv/setcomment/(.*?)/(.*?)/", SetComment),
    (r"/admin/kv/setarticles/(.*?)/", SetArticles),
    (r"/admin/kv/setarticle/(.*?)/(.*?)/", SetArticle),
    (r"/admin/kv/setuser/(.*?)/", SetUser),
    (r"/admin/kv/setlink/(.*?)/", SetLink),
    (r"/admin/kvdb$", KVDBAdmin),
    (r"/admin/kvdb/save/", KVDBSave),
    (r"/admin/kvdb/del/", KVDBDel),
    (r"/admin/kvdb/download/", KVDBDownload),
    ]
else:
    urls = []

#yobin add kvdb panel 20160824 begin
urls += [
	(r'/kvdbpanel/kv/', kvpanel_index),
	(r'/kvdbpanel/kv/set/', kvpanel_set),
	(r'/kvdbpanel/kv/del/', kvpanel_del),
	(r'/kvdbpanel/kv/get/', kvpanel_get),
]
#yobin add kvdb panel 20160824 end

urls += [
    (r"/admin/", HomePage),
    (r"/admin/login", Login),
    (r"/admin/logout", Logout),
    (r"/admin/403", Forbidden),
    (r"/admin/add_post", AddPost),
    (r"/admin/edit_post/(\d*)", EditPost),
    (r"/admin/del_post/(\d+)", DelPost),
    (r"/admin/comment/(\d*)", EditComment),
    (r"/admin/flushdata", FlushData),
    (r"/task/pingrpctask", PingRPCTask),
    (r"/task/pingrpc/(\d+)", PingRPC),
    (r"/task/sendmail", SendMail),
    (r"/install", Install),
    (r"/admin/fileupload", FileUpload),
    (r"/admin/links", LinkBroll),
    (r"/admin/setting", BlogSetting),
    #(r"/admin/setting2", BlogSetting2),
    (r"/admin/setting3", BlogSetting3),
    (r"/admin/storage", StorageSetting),
    #(r"/admin/moveblog", MovePost),
    (r"/admin/markitup/preview", PostPrevewPage),
    (r".*", NotFoundPage)
]
