# -*- coding: utf-8 -*-
import logging
import re
from hashlib import md5

from time import time
from datetime import datetime

from common import *
from setting import *

try:
    from tornado import database
except:
    pass

import markdown2 as markdown
from plugins import parse_text

##
##数据库配置信息
if debug or MYSQL_TO_KVDB_SUPPORT:
    #已经在setting里设置了
    pass
else:
    import sae.const
    MYSQL_DB = sae.const.MYSQL_DB
    MYSQL_USER = sae.const.MYSQL_USER
    MYSQL_PASS = sae.const.MYSQL_PASS
    MYSQL_HOST_M = sae.const.MYSQL_HOST
    MYSQL_HOST_S = sae.const.MYSQL_HOST_S
    MYSQL_PORT = sae.const.MYSQL_PORT

#主数据库 进行Create,Update,Delete 操作
#从数据库 读取

##
#HTML_REG = re.compile(r"""<[^>]+>""", re.I|re.M|re.S)

if MYSQL_TO_KVDB_SUPPORT:
    mdb = None
    sdb = None
else:
    mdb = database.Connection("%s:%s"%(MYSQL_HOST_M,str(MYSQL_PORT)), MYSQL_DB,MYSQL_USER, MYSQL_PASS, max_idle_time = MAX_IDLE_TIME)
    sdb = database.Connection("%s:%s"%(MYSQL_HOST_S,str(MYSQL_PORT)), MYSQL_DB,MYSQL_USER, MYSQL_PASS, max_idle_time = MAX_IDLE_TIME)

###

def post_list_format(posts):
    if MYSQL_TO_KVDB_SUPPORT:
        if posts:
            for obj in posts:
                obj['absolute_url'] = '%s/topic/%s/%s' % (BASE_URL, str(obj['id']), slugfy(obj['title']))
                obj['taglist'] = ', '.join(["""<a href="%s/tag/%s/" rel="tag">%s</a>"""%(BASE_URL, tag, tag) for tag in obj['tags'].split(',')])
                if '<!--more-->' in obj['content']:
                    obj['shorten_content'] = obj['content'].split('<!--more-->')[0]
                else:
                    obj['shorten_content'] = HTML_REG.sub('',obj['content'][:SHORTEN_CONTENT_WORDS])
                obj['add_time_fn'] = time_from_now(int(obj['add_time']))
    else:
        for obj in posts:
            obj.absolute_url = '%s/topic/%d/%s' % (BASE_URL, obj.id, slugfy(obj.title))
            obj.taglist = ', '.join(["""<a href="%s/tag/%s/" rel="tag">%s</a>"""%(BASE_URL, tag, tag) for tag in obj.tags.split(',')])
            if '<!--more-->' in obj.content:
                obj.shorten_content = obj.content.split('<!--more-->')[0]
            else:
                obj.shorten_content = HTML_REG.sub('',obj.content[:SHORTEN_CONTENT_WORDS])
            obj.add_time_fn = time_from_now(int(obj.add_time))
    return posts

def post_detail_formate_kv(obj):
    if obj:
        #slug = slugfy(obj['title'])#yobin 20160718
        slug = obj['title']
        obj['slug'] = slug
        obj['absolute_url'] = '%s/topic/%s/%s' % (BASE_URL, str(obj['id']), slug)
        obj['shorten_url'] = '%s/t/%s' % (BASE_URL, str(obj['id']))

        if getAttr('MARKDOWN'):
        #if False:#yobin 20131023
            obj['highlight'] = False
            obj['content'] =  markdown.markdown(parse_text(obj['content']))
        else:
            if '[/code]' in obj['content']:
                obj['highlight'] = True
            else:
                obj['highlight'] = False
            obj['content'] = tran_content(obj['content'], obj['highlight'])
        obj['taglist'] = ', '.join(["""<a href="%s/tag/%s/" rel="tag">%s</a>"""%(BASE_URL, tag, tag) for tag in obj['tags'].split(',')])
        obj['add_time_fn'] = time_from_now(int(obj['add_time']))
        obj['last_modified'] = timestamp_to_datetime(int(obj['edit_time']))
        obj['keywords'] = obj['tags']
        obj['description'] = HTML_REG.sub('',obj['content'][:DESCRIPTION_CUT_WORDS])

        #get prev and next obj
        obj['prev_obj'] = Article.get_prev_article(str(obj['id']))
        if obj['prev_obj']:
            obj['prev_obj']['slug'] = slugfy(obj['prev_obj']['title'])
        obj['next_obj'] = Article.get_next_article(str(obj['id']))
        if obj['next_obj']:
            obj['next_obj']['slug'] = slugfy(obj['next_obj']['title'])
        #get relative obj base tags
        obj['relative'] = []
        if obj['tags']:
            idlist = []
            getit = False
            for tag in obj['tags'].split(','):
                tagobj = Tag.get_tag_by_name(tag)
                if tagobj:
                    pids = tagobj.split(',')
                else:
                    pids = []
                for pid in pids:
                    if pid != str(obj['id']) and pid not in idlist:
                        idlist.append(pid)
                        if len(idlist) >= RELATIVE_POST_NUM:
                            getit = True
                            break
                if getit:
                    break
            #
            if idlist:
                obj['relative'] = Article.get_related_articles(idlist)
                if obj['relative']:
                    for robj in obj['relative']:
                        robj['slug'] = slugfy(robj['title'])
        #get comment
        obj['coms'] = []
        if int(obj['comment_num']) > 0:
            if int(obj['comment_num']) >= EACH_PAGE_COMMENT_NUM:
                first_limit = EACH_PAGE_COMMENT_NUM
            else:
                first_limit = int(obj['comment_num'])
            obj['coms'] = Comment.get_post_page_comments_by_id( obj['id'], 0, first_limit )
    return obj

def post_detail_formate(obj):
    if obj:
        slug = slugfy(obj.title)
        obj.slug = slug
        obj.absolute_url = '%s/topic/%d/%s' % (BASE_URL, obj.id, slug)
        obj.shorten_url = '%s/t/%s' % (BASE_URL, obj.id)

        if getAttr('MARKDOWN'):
        #if False:#yobin 20131023
            obj.highlight = False
            obj.content =  markdown.markdown(parse_text(obj.content))
        else:
            if '[/code]' in obj.content:
                obj.highlight = True
            else:
                obj.highlight = False
            obj.content = tran_content(obj.content, obj.highlight)
        obj.taglist = ', '.join(["""<a href="%s/tag/%s/" rel="tag">%s</a>"""%(BASE_URL, tag, tag) for tag in obj.tags.split(',')])
        obj.add_time_fn = time_from_now(int(obj.add_time))
        obj.last_modified = timestamp_to_datetime(obj.edit_time)
        obj.keywords = obj.tags
        obj.description = HTML_REG.sub('',obj.content[:DESCRIPTION_CUT_WORDS])
        #get prev and next obj
        obj.prev_obj = sdb.get('SELECT `id`,`title` FROM `sp_posts` WHERE `id` > %s LIMIT 1' % str(obj.id))
        if obj.prev_obj:
            obj.prev_obj.slug = slugfy(obj.prev_obj.title)
        obj.next_obj = sdb.get('SELECT `id`,`title` FROM `sp_posts` WHERE `id` < %s ORDER BY `id` DESC LIMIT 1' % str(obj.id))
        if obj.next_obj:
            obj.next_obj.slug = slugfy(obj.next_obj.title)
        #get relative obj base tags
        obj.relative = []
        if obj.tags:
            idlist = []
            getit = False
            for tag in obj.tags.split(','):
                tagobj = Tag.get_tag_by_name(tag)
                if tagobj and tagobj.content:
                    pids = tagobj.content.split(',')
                else:
                    pids = []
                for pid in pids:
                    if pid != str(obj.id) and pid not in idlist:
                        idlist.append(pid)
                        if len(idlist) >= RELATIVE_POST_NUM:
                            getit = True
                            break
                if getit:
                    break
            #
            if idlist:
                obj.relative = sdb.query('SELECT `id`,`title` FROM `sp_posts` WHERE `id` in(%s) LIMIT %s' % (','.join(idlist), str(len(idlist))))
                if obj.relative:
                    for robj in obj.relative:
                        robj.slug = slugfy(robj.title)
        #get comment
        obj.coms = []
        if obj.comment_num >0:
            if obj.comment_num >= EACH_PAGE_COMMENT_NUM:
                first_limit = EACH_PAGE_COMMENT_NUM
            else:
                first_limit = obj.comment_num
            obj.coms = Comment.get_post_page_comments_by_id( obj.id, 0, first_limit )
    return obj

def comment_format(objs):
    if MYSQL_TO_KVDB_SUPPORT:
        for obj in objs:
            if GRAVATAR_SUPPORT:
                obj['gravatar'] = 'http://www.gravatar.com/avatar/%s'%md5(obj['email']).hexdigest()
            else:
                obj['gravatar'] = ''
                obj['add_time'] = time_from_now(int(obj['add_time']))
                if int(obj['visible']):
                    obj['short_content'] = HTML_REG.sub('',obj['content'][:RECENT_COMMENT_CUT_WORDS])
                else:
                    obj['short_content'] = 'Your comment is awaiting moderation.'[:RECENT_COMMENT_CUT_WORDS]
                obj['content'] = obj['content'].replace('\n','<br/>')
    else:
        for obj in objs:
            if GRAVATAR_SUPPORT:
                obj.gravatar = 'http://www.gravatar.com/avatar/%s'%md5(obj.email).hexdigest()
            else:
                obj.gravatar = ''
                obj.add_time = time_from_now(int(obj.add_time))

                if obj.visible:
                    obj.short_content = HTML_REG.sub('',obj.content[:RECENT_COMMENT_CUT_WORDS])
                else:
                    obj.short_content = 'Your comment is awaiting moderation.'[:RECENT_COMMENT_CUT_WORDS]

                obj.content = obj.content.replace('\n','<br/>')
    return objs

###以下是各个数据表的操作

###########

class Article():
    def del_article_by_id(self, id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id:
                k = 'kv_artis'
                v = getkv(k)
                if v:
                    idlist = v.split(',')
                    idlist.remove(str(id))
                    try:
                        idlist.remove('')
                    except:
                        pass
                    if len(idlist):
                        setkv(k,','.join(idlist))
                    else:
                        delkv(k)

    def add_newid_to_artis(self,newid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_artis'
            v = getkv(k)
            if v:
                idlist = v.split(',')
                idlist.append(str(newid))
                setkv(k,','.join(idlist))
            else:
                newid = '1'
                setkv(k,newid)

    def get_totalnum_arti(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_artis'
            v = getkv(k)
            if v:
                return len(v.split(','))
        return 0

    def get_artilist(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_artis'
            v = getkv(k)
            if v:
                return v.split(',')
            return None

    def get_article(self,id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id:
                k = 'kv_arti_%s' % (str(id))
                v = getkv(k)
                if v:
                    return decode_dict(v)
        return None

    def get_next_article(self,id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id:
                idlist = self.get_artilist()
                if idlist:
                    basepos = idlist.index(str(id))
                    if basepos == len(idlist) - 1:
                        return None
                    return self.get_article(idlist[basepos+1])
        return None

    def get_prev_article(self,id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id:
                idlist = self.get_artilist()
                if idlist:
                    basepos = idlist.index(str(id))
                    if basepos == 0:
                        return None
                    return self.get_article(idlist[basepos-1])
        return None

    def get_related_articles(self,idlist = []):
        if MYSQL_TO_KVDB_SUPPORT:
            if idlist:
                return [self.get_article(id) for id in idlist]
        return None

    def set_article(self,id = '',arti=''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id and arti:
                k = 'kv_arti_%s' % (str(id))
                setkv(k,arti)

    def set_articles(self,arti=''):
        if MYSQL_TO_KVDB_SUPPORT:
            if arti:
                k = 'kv_artis'
                setkv(k,arti)

    def get_max_id(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_artis'
            v = getkv(k)
            if v:
                return str(v.split(',')[-1])
            return '0'
        else:
            sdb._ensure_connected()
            maxobj = sdb.query("select max(id) as maxid from `sp_posts`")
            return str(maxobj[0]['maxid'])

    def get_last_post_add_time(self):
        if MYSQL_TO_KVDB_SUPPORT:
            id  = self.get_max_id()
            obj = self.get_article(id)
            if obj:
                return datetime.fromtimestamp(int(obj['add_time']))
            else:
                return datetime.utcnow() + timedelta(hours =+ 8)
        else:
            sdb._ensure_connected()
            obj = sdb.get('SELECT `add_time` FROM `sp_posts` ORDER BY `id` DESC LIMIT 1')
            if obj:
                return datetime.fromtimestamp(obj.add_time)
            else:
                return datetime.utcnow() + timedelta(hours =+ 8)

    def count_all_post(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_artis'
            v = getkv(k)
            if v:
                return len(v.split(','))
            return 0
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT COUNT(*) AS postnum FROM `sp_posts`')[0]['postnum']

    def get_post_for_homepage(self):
        if MYSQL_TO_KVDB_SUPPORT:
            artilist = self.get_artilist()
            if artilist:
                artilist.reverse()
                return post_list_format([self.get_article(id) for id in artilist[:EACH_PAGE_POST_NUM]])
            return None
        else:
            sdb._ensure_connected()
            return post_list_format(sdb.query("SELECT * FROM `sp_posts` ORDER BY `id` DESC LIMIT %s" % str(EACH_PAGE_POST_NUM)))

    def get_page_posts(self, direction = 'next', page = 1 , base_id = '', limit = EACH_PAGE_POST_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            artilist = self.get_artilist()
            artilist.reverse()
            if artilist:
                basepos = artilist.index(base_id)
                if direction == 'next':
                    new_artilist = artilist[basepos+1:basepos+EACH_PAGE_POST_NUM+1]
                else:
                    if basepos - EACH_PAGE_POST_NUM < 0:
                        new_artilist = artilist[:EACH_PAGE_POST_NUM]
                    else:
                        new_artilist = artilist[basepos-EACH_PAGE_POST_NUM:basepos]
                    new_artilist.reverse()
                return post_list_format([self.get_article(id) for id in new_artilist])
        else:
            sdb._ensure_connected()
            if direction == 'next':
                return post_list_format(sdb.query("SELECT * FROM `sp_posts` WHERE `id` < %s ORDER BY `id` DESC LIMIT %s" % (str(base_id), str(EACH_PAGE_POST_NUM))))
            else:
                return post_list_format(sdb.query("SELECT * FROM `sp_posts` WHERE `id` > %s ORDER BY `id` ASC LIMIT %s" % (str(base_id), str(EACH_PAGE_POST_NUM))))

    def get_article_by_id_detail(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            obj = self.get_article(id)
            return post_detail_formate_kv(obj)
        else:
            sdb._ensure_connected()
            return post_detail_formate(sdb.get('SELECT * FROM `sp_posts` WHERE `id` = %s LIMIT 1' % str(id)))

    #yobin add 20131021 for weixin begin
    #模糊查询文章
    def get_article_by_keyword(self, keyword):
        return ''
        sdb._ensure_connected()
        keyword_quote = '%'+ keyword +'%'
        return post_detail_formate(sdb.get('SELECT * FROM `sp_posts` WHERE `title` LIKE %s OR `tags` LIKE %s LIMIT 1' , str(keyword_quote), str(keyword_quote)))

    # 最新文章
    def get_articles_by_latest(self):
        if MYSQL_TO_KVDB_SUPPORT:
            artilist = self.get_artilist()
            if artilist:
                artilist.reverse()
                return [post_detail_formate_kv(self.get_article(id)) for id in artilist[:WX_MAX_ARTICLE]]
            return None
        else:
            sdb._ensure_connected()
            posts = sdb.query('SELECT * FROM `sp_posts` ORDER BY `id` DESC LIMIT %d' % (WX_MAX_ARTICLE))
            return [post_detail_formate(post) for post in posts]

    def get_articles_list(self):
        if MYSQL_TO_KVDB_SUPPORT:
            artilist = self.get_artilist()
            if artilist:
                artilist.reverse()
                return [self.get_article(id) for id in artilist[:WX_MAX_ARTICLE]]
            return None
        else:
            sdb._ensure_connected()
            article_list = sdb.query('SELECT `id`,`title`,`category` FROM `sp_posts` ORDER BY `id` DESC LIMIT %d' % (WX_MAX_ARTICLE))
            return article_list
    #yobin add 20131021 for weixin end

    def get_article_by_id_simple(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            return self.get_article(id)
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT `id`,`title`,`comment_num`,`closecomment`,`password` FROM `sp_posts` WHERE `id` = %s LIMIT 1' % str(id))

    def get_article_by_id_edit(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            return self.get_article(id)
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_posts` WHERE `id` = %s LIMIT 1' % str(id))

    def add_new_article(self, params):
        if MYSQL_TO_KVDB_SUPPORT:
            newid = int(self.get_max_id()) + 1

            self.add_newid_to_artis(str(newid))

            k = 'kv_arti_%s' % (str(newid))
            params['id'] = str(newid)
            params['comment_num'] = '0'
            setkv(k,encode_dict(params))

            return str(newid)
        else:
            query = "INSERT INTO `sp_posts` (`category`,`title`,`content`,`closecomment`,`tags`,`password`,`add_time`,`edit_time`,`archive`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            mdb._ensure_connected()
            return mdb.execute(query, params['category'], params['title'], params['content'], params['closecomment'], params['tags'], params['password'], params['add_time'], params['edit_time'], params['archive'])

    def update_post_edit(self, params):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_arti_%s' % (str(params['id']))
            setkv(k,encode_dict(params))
            return params['id']
        else:
            query = "UPDATE `sp_posts` SET `category` = %s, `title` = %s, `content` = %s, `closecomment` = %s, `tags` = %s, `password` = %s, `edit_time` = %s WHERE `id` = %s LIMIT 1"
            mdb._ensure_connected()
            mdb.execute(query, params['category'], params['title'], params['content'], params['closecomment'], params['tags'], params['password'], params['edit_time'], params['id'])
            ### update 返回不了 lastrowid，直接返回 post id
            return params['id']

    def update_post_comment(self, num = 1,id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_arti_%s' % (str(id))
            v = getkv(k)
            if v:
                pdict = decode_dict(v)
                pdict['comment_num'] = str(num)
                setkv(k,encode_dict(pdict))
        else:
            query = "UPDATE `sp_posts` SET `comment_num` = %s WHERE `id` = %s LIMIT 1"
            mdb._ensure_connected()
            return mdb.execute(query, num, id)

    def get_post_for_sitemap(self, ids=[]):
        if MYSQL_TO_KVDB_SUPPORT:
            return [self.get_article(id) for id in ids]
        else:
            sdb._ensure_connected()
            return sdb.query("SELECT `id`,`edit_time` FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (','.join(ids), str(len(ids))))

    def del_post_by_id(self, id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_arti_%s' % (str(id))
            delkv(k)
            self.del_article_by_id(str(id))
            Comment.del_comm_by_postid(id)
        else:
            if id:
                obj = self.get_article_by_id_simple(id)
                if obj:
                    limit = obj.comment_num
                    mdb._ensure_connected()
                    mdb.execute("DELETE FROM `sp_posts` WHERE `id` = %s LIMIT 1", id)
                    mdb.execute("DELETE FROM `sp_comments` WHERE `postid` = %s LIMIT %s", id, limit)

Article = Article()

class Comment():
    def del_comm_by_postid(self, postid = ''):
        if postid:
            k = 'kv_pcomm'
            v = getkv(k)
            if v:
                pcdict = decode_dict(v)
                try:
                    idlist = pcdict[postid].split(',')
                    pcdict.pop(postid)
                    setkv(k,encode_dict(pcdict))

                    for id in idlist:
                        k = 'kv_comm_%s' % (str(id))
                        delkv(k)
                except Exception , e:
                    print 'del_comm_by_postid',e

    def del_comm(self,id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id:
                postid = ''
                k = 'kv_comm_%s' % (str(id))
                v = getkv(k)
                if v:
                    cdict = decode_dict(v)
                    postid = cdict['postid']
                delkv(k)

                k = 'kv_comms'
                v = getkv(k)
                if v:
                    try:
                        clist = v.split(',')
                        clist.remove(id)
                        clist.remove('')
                    except:
                        pass
                    if len(clist):
                        setkv(k,','.join(clist))

                if postid:
                    k = 'kv_pcomm'
                    v = getkv(k)
                    if v:
                        pcdict = decode_dict(v)
                        idlist = pcdict[postid].split(',')
                        try:
                            idlist.remove(id)
                            idlist.remove('')
                        except:
                            pass
                        if len(idlist):
                            pcdict[postid] = ','.join(idlist)
                        else:
                            pcdict.pop(postid)
                        setkv(k,encode_dict(pcdict))

    def set_comm(self,id,comm):
        if MYSQL_TO_KVDB_SUPPORT:
            if id and comm:
                k = 'kv_comm_%s' % (str(id))
                setkv(k,comm)

    def set_comms(self,comm):
        if MYSQL_TO_KVDB_SUPPORT:
            if comm:
                k = 'kv_comms'
                setkv(k,comm)

    def set_pcomm(self,pcomm):
        if MYSQL_TO_KVDB_SUPPORT:
            if pcomm:
                k = 'kv_pcomm'
                setkv(k,pcomm)

    def del_comment_by_id(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            cobj = self.get_comment_by_id(id)
            postid = cobj['postid']
            pobj = Article.get_article_by_id_edit(postid)
            if pobj:
                Article.update_post_comment( int(pobj['comment_num'])-1, postid)

            self.del_comm(id)
        else:
            cobj = self.get_comment_by_id(id)
            postid = cobj.postid
            pobj = Article.get_article_by_id_edit(postid)

            mdb._ensure_connected()
            mdb.execute("DELETE FROM `sp_comments` WHERE `id` = %s LIMIT 1", id)
            if pobj:
                Article.update_post_comment( pobj.comment_num-1, postid)

    def get_comment_by_id(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_comm_%s' % (str(id))
            v = getkv(k)
            if v:
                return decode_dict(v)
            return None
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_comments` WHERE `id` = %s LIMIT 1' % str(id))

    def get_recent_comments(self, limit = RECENT_COMMENT_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_comms'
            v = getkv(k)
            objs = []
            if v:
                #return comment_format([self.get_comment_by_id(id) for id in v.split(',')[-limit:],reverse=True)
                idlist = v.split(',')
                idlist.reverse()
                for id in idlist[:limit]:
                    objs.append(self.get_comment_by_id(id))
            return comment_format(objs)
        else:
            sdb._ensure_connected()
            return comment_format(sdb.query('SELECT * FROM `sp_comments` ORDER BY `id` DESC LIMIT %s' % str(limit)))

    def get_post_page_comments_by_id(self, postid = 0, min_comment_id = 0, limit = EACH_PAGE_COMMENT_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_pcomm'
            v = getkv(k)
            if v:
                pcdict = decode_dict(v)
                if not str(postid) in pcdict:
                    return None
                idlist = pcdict[str(postid)].split(',')
                objs = []
                if min_comment_id == 0:
                    for loop,id in enumerate(idlist):
                        if loop == limit:
                            break
                        objs.append(self.get_comment_by_id(id))
                else:
                    loop = 0
                    for id in idlist:
                        obj = self.get_comment_by_id(id)
                        if int(obj['id']) > min_comment_id:
                            objs.append(obj)
                            loop += 1
                            if loop == limit:
                                break
                return comment_format(objs)
            return None
        else:
            if min_comment_id == 0:
                sdb._ensure_connected()
                return comment_format(sdb.query('SELECT * FROM `sp_comments` WHERE `postid`= %s ORDER BY `id` DESC LIMIT %s' % (str(postid), str(limit))))
            else:
                sdb._ensure_connected()
                return comment_format(sdb.query('SELECT * FROM `sp_comments` WHERE `postid`= %s AND `id` < %s ORDER BY `id` DESC LIMIT %s' % (str(postid), str(min_comment_id), str(limit))))

    def add_new_comment(self, params):
        if MYSQL_TO_KVDB_SUPPORT:
            newid = 0
            k = 'kv_comms'
            v = getkv(k)
            if v:
                idlist = v.split(',')
                newid  = int(idlist[-1]) + 1
                idlist.append(str(newid))
                setkv(k,','.join(idlist))
            else:
                newid = '1'
                setkv(k,newid)

            k = 'kv_comm_%s' % (str(newid))
            params['id'] = str(newid)
            setkv(k,encode_dict(params))

            k = 'kv_pcomm'
            v = getkv(k)
            if v:
                pcdict = decode_dict(v)
                postid = str(params['postid'])
                if pcdict.has_key(postid):
                    pcdict[postid] = '%s,%s' % (pcdict[postid],str(newid))
                else:
                    pcdict[postid] = '%s' % (str(newid))
            else:
                pcdict[postid] = '%s' % (str(newid))
            setkv(k,encode_dict(pcdict))
            return str(newid)
        else:
            query = "INSERT INTO `sp_comments` (`postid`,`author`,`email`,`url`,`visible`,`add_time`,`content`) values(%s,%s,%s,%s,%s,%s,%s)"
            mdb._ensure_connected()
            return mdb.execute(query, params['postid'], params['author'], params['email'], params['url'], params['visible'], params['add_time'], params['content'])

    def update_comment_edit(self, params):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_comm_%s' % (str(params['id']))
            setkv(k,encode_dict(params))
            return params['id']
        else:
            query = "UPDATE `sp_comments` SET `author` = %s, `email` = %s, `url` = %s, `visible` = %s, `content` = %s WHERE `id` = %s LIMIT 1"
            mdb._ensure_connected()
            mdb.execute(query, params['author'], params['email'], params['url'], params['visible'], params['content'], params['id'])
            ### update 返回不了 lastrowid，直接返回 id
            return params['id']

Comment = Comment()

class Link():
    def set_link(self, values = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if values:
                k = 'kv_links'
                setkv(k,values)

    def get_all_links(self, limit = LINK_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_links'
            v = getkv(k)
            if v:
                return decode_dictlist(v)
            return None
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT * FROM `sp_links` ORDER BY `displayorder` DESC LIMIT %s' % str(limit))

    def add_new_link(self, params):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_links'
            v = getkv(k)
            if v:
                v = decode_dictlist(v)
                params['id'] = len(v) + 1
                v.append(params)
                setkv(k,encode_dictlist(v))
            else:
                params['id'] = 1
                setkv(k,encode_dictlist(list(params)))
        else:
            query = "INSERT INTO `sp_links` (`displayorder`,`name`,`url`) values(%s,%s,%s)"
            mdb._ensure_connected()
            mdb.execute(query, params['displayorder'], params['name'], params['url'])

    def update_link_edit(self, params):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_links'
            v = getkv(k)
            if v:
                v = decode_dictlist(v)
                tmplst = []
                for i in v:
                    if str(i['id']) == str(params['id']):
                        tmplst.append(params)
                    else:
                        tmplst.append(i)
                setkv(k,encode_dictlist(tmplst))
        else:
            query = "UPDATE `sp_links` SET `displayorder` = %s, `name` = %s, `url` = %s WHERE `id` = %s LIMIT 1"
            mdb._ensure_connected()
            mdb.execute(query, params['displayorder'], params['name'], params['url'], params['id'])

    def del_link_by_id(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_links'
            v = getkv(k)
            if v:
                v = decode_dictlist(v)
                tmplst = []
                index = 0
                for i in v:
                    if not str(i['id']) == str(id):
                        i['id'] = index
                        tmplst.append(i)
                        index += 1
                setkv(k,encode_dictlist(tmplst))
        else:
            mdb._ensure_connected()
            mdb.execute("DELETE FROM `sp_links` WHERE `id` = %s LIMIT 1", id)

    def get_link_by_id(self, id):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_links'
            v = getkv(k)
            if v:
                v = decode_dictlist(v)
                for i in v:
                    if str(i['id']) == str(id):
                        return i
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_links` WHERE `id` = %s LIMIT 1' % str(id))

Link = Link()

class Category():
    def set_cats(self,cats = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_cats'
            if cats:
                setkv(k,cats)

    def get_all_cat_name(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_cats'
            v = getkv(k)
            if v:
                catdict = decode_dict(v)
                cat_list = sorted(catdict.keys())
                return [(item,len(catdict[item].split(','))) for item in cat_list]
            return None
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT `name`,`id_num`,`id` FROM `sp_category` ORDER BY `id` DESC')

    def get_all_cat(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_cats'
            v = getkv(k)
            if v:
                catdict = decode_dict(v)
                return catdict.items()
            return None
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT * FROM `sp_category` ORDER BY `id` DESC')

    def get_all_cat_id(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_cats'
            v = getkv(k)
            if v:
                catdict = decode_dict(v)
                cat_list = sorted(catdict.keys())
                mylist = ["%d" % (loop) for loop,cat in enumerate(cat_list)]
                return mylist
            return []
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT `id` FROM `sp_category` ORDER BY `id` DESC')

    def get_cat_by_name(self, name = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name:
                name = name.encode('utf-8')
                k = 'kv_cats'
                v = getkv(k)
                if v:
                    catdict = decode_dict(v)
                    if catdict:
                        if name in catdict:
                            return catdict[name]
            return ''
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_category` WHERE `name` = \'%s\' LIMIT 1' % name)

    def get_all_post_num(self, name = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name:
                k = 'kv_cats'
                v = getkv(k)
                if v:
                    obj = self.get_cat_by_name(name)
                    if obj:
                        return len(obj.split(','))
            return 0
        else:
            obj = self.get_cat_by_name(name)
            if obj and obj.content:
                return len(obj.content.split(','))
            return 0

    #yobin 20131023 added for weixin begin
    def get_cat_page_posts_by_cid(self, cid = '', page = 1, limit = WX_MAX_ARTICLE):
        if MYSQL_TO_KVDB_SUPPORT:
            if cid:
                k = 'kv_cats'
                v = getkv(k)
                if v:
                    obj = self.get_cat_by_id(cid)
                    if obj:
                        page = int(page)
                        idlist = obj[2].split(',')
                        getids = idlist[limit*(page-1):limit*page]
                        return post_list_format(Article.get_related_articles(getids))
            return []
        else:
            obj = self.get_cat_by_id(cid)
            if obj:
                page = int(page)
                idlist = obj.content.split(',')
                getids = idlist[limit*(page-1):limit*page]
                sdb._ensure_connected()
                return post_list_format(sdb.query("SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (','.join(getids), str(len(getids)))))
            return []
    #yobin 20131023 added for weixin end

    def get_cat_page_posts(self, name = '', page = 1, limit = EACH_PAGE_POST_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            if name:
                obj = self.get_cat_by_name(name)
                if obj:
                    page = int(page)
                    idlist = obj.split(',')
                    getids = idlist[limit*(page-1):limit*page]
                    return post_list_format(Article.get_related_articles(getids))
            return []
        else:
            obj = self.get_cat_by_name(name)
            if obj:
                page = int(page)
                idlist = obj.content.split(',')
                getids = idlist[limit*(page-1):limit*page]
                sdb._ensure_connected()
                return post_list_format(sdb.query("SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (','.join(getids), str(len(getids)))))
            return []

    def add_postid_to_cat(self, name = '', postid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name and postid:
                name = name.encode('utf-8')
                k = 'kv_cats'
                v = getkv(k)
                if v:
                    catdict = decode_dict(v)
                    if catdict.has_key(name):
                        catdict[name] = '%s,%s' % (str(postid),catdict[name])
                    else:
                        catdict[name] = str(postid)
                    setkv(k,encode_dict(catdict))
        else:
            mdb._ensure_connected()
            #因为 UPDATE 时无论有没有影响行数，都返回0，所以这里要多读一次（从主数据库读）
            obj = mdb.get('SELECT * FROM `sp_category` WHERE `name` = \'%s\' LIMIT 1' % name)

            if obj:
                query = "UPDATE `sp_category` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
                mdb.execute(query, "%s,"%postid, obj.id)
            else:
                query = "INSERT INTO `sp_category` (`name`,`id_num`,`content`) values(%s,1,%s)"
                mdb.execute(query, name, postid)

    def remove_postid_from_cat(self, name = '', postid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name and postid:
                name = name.encode('utf-8')
                k = 'kv_cats'
                v = getkv(k)
                if v:
                    catdict = decode_dict(v)
                    idlist = catdict[name].split(',')
                    try:
                        idlist.remove(postid)
                        idlist.remove('')
                    except:
                        pass

                    if len(idlist) == 0:
                        catdict.pop(name)
                    else:
                        catdict[name] = ','.join(idlist)
                    setkv(k,encode_dict(catdict))
        else:
            mdb._ensure_connected()
            if name:
                obj = mdb.get('SELECT * FROM `sp_category` WHERE `name` = \'%s\' LIMIT 1' % name)
                if obj:
                    idlist = obj.content.split(',')
                    if postid in idlist:
                        idlist.remove(postid)
                        try:
                            idlist.remove('')
                        except:
                            pass
                        if len(idlist) == 0:
                            mdb.execute("DELETE FROM `sp_category` WHERE `id` = %s LIMIT 1", str(obj.id))
                        else:
                            query = "UPDATE `sp_category` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                            mdb.execute(query, len(idlist), ','.join(idlist), str(obj.id))
                    else:
                        pass
                else:
                    print 'not obj'
            else:
                print 'not name'

    def get_cat_by_id(self, id = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if id:
                k = 'kv_cats'
                v = getkv(k)
                if v:
                    catdict = decode_dict(v)
                    cat_list = sorted(catdict.keys())
                    return (id,cat_list[int(id)-1],catdict[cat_list[int(id)-1]])
            return None
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_category` WHERE `id` = %s LIMIT 1' % str(id))

    def get_sitemap_by_id(self, id=''):
        if MYSQL_TO_KVDB_SUPPORT:
            obj = self.get_cat_by_id(id)
            if not obj:
                return ''

            urlstr = """<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>\n """
            urllist = []
            urllist.append('<?xml version="1.0" encoding="UTF-8"?>\n')
            urllist.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            urllist.append(urlstr%( "%s/c/%s" % (BASE_URL, str(obj[0])), cnnow().strftime("%Y-%m-%dT%H:%M:%SZ"), 'daily', '0.8'))

            objs = Article.get_post_for_sitemap(obj[2].split(','))
            for p in objs:
                if p:
                    urllist.append(urlstr%("%s/t/%s" % (BASE_URL, str(p['id'])), timestamp_to_datetime(p['edit_time']).strftime("%Y-%m-%dT%H:%M:%SZ"), 'weekly', '0.6'))
            urllist.append('</urlset>')
            return ''.join(urllist)
        else:
            obj = self.get_cat_by_id(id)
            if not obj:
                return ''
            if not obj.content:
                return ''

            urlstr = """<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>\n """
            urllist = []
            urllist.append('<?xml version="1.0" encoding="UTF-8"?>\n')
            urllist.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

            urllist.append(urlstr%( "%s/c/%s" % (BASE_URL, str(obj.id)), cnnow().strftime("%Y-%m-%dT%H:%M:%SZ"), 'daily', '0.8'))

            objs = Article.get_post_for_sitemap(obj.content.split(','))
            for p in objs:
                if p:
                    urllist.append(urlstr%("%s/t/%s" % (BASE_URL, str(p.id)), timestamp_to_datetime(p.edit_time).strftime("%Y-%m-%dT%H:%M:%SZ"), 'weekly', '0.6'))

            urllist.append('</urlset>')
            return ''.join(urllist)

Category = Category()

class Tag():
    def set_tags(self,tags = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            if tags:
                setkv(k,tags)

    def get_all_tag_name(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v:
                tagdict = decode_dict(v)
                return tagdict.keys()
            return None
        else:
            #for add/edit post
            sdb._ensure_connected()
            return sdb.query('SELECT `name` FROM `sp_tags` ORDER BY `id` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_all_tag(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v:
                tagdict = decode_dict(v)
                return tagdict.items()
            return None
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT * FROM `sp_tags` ORDER BY `id` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_hot_tag_name(self):
        #for sider
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v:
                tagdict = decode_dict(v)
                L = tagdict.items()
                L.sort(lambda x,y:cmp(len(x[1]),len(y[1])),reverse=True)
                return [(item[0],len(item[1].split(','))) for item in L]
            return None
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT `name`,`id_num` FROM `sp_tags` ORDER BY `id_num` DESC LIMIT %d' % HOT_TAGS_NUM)

    def get_tag_by_name(self, name = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v and name:
                try:
                    name = name.encode('utf-8')
                    tagdict = decode_dict(v)
                    if name in tagdict:
                        return tagdict[name]
                    else:
                        print 'get_tag_by_name() name = %s not in tagdict' % (name)
                except Exception , e:
                    print 'get_tag_by_name() exception,name = %s, e=%s' % (name,e)
            return None
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_tags` WHERE `name` = \'%s\' LIMIT 1' % name)

    def get_all_post_num(self, name = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v and name:
                obj = self.get_tag_by_name(name)
                if obj:
                    return len(obj.split(','))
            return 0
        else:
            obj = self.get_tag_by_name(name)
            if obj and obj.content:
                return len(obj.content.split(','))
            return 0

    def get_tag_page_posts(self, name = '', page = 1, limit = EACH_PAGE_POST_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v and name:
                tagdict = decode_dict(v)
                obj = self.get_tag_by_name(name)
                if obj:
                    page = int(page)
                    idlist = obj.split(',')
                    getids = idlist[limit*(page-1):limit*page]
                    return post_list_format(Article.get_related_articles(getids))
            return []
        else:
            obj = self.get_tag_by_name(name)
            if obj and obj.content:
                page = int(page)
                idlist = obj.content.split(',')
                getids = idlist[limit*(page-1):limit*page]
                sdb._ensure_connected()
                return post_list_format(sdb.query("SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (','.join(getids), len(getids))))
            return []

    def add_postid_to_tags(self, tags = [], postid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_tags'
            v = getkv(k)
            if v:
                tagdict = decode_dict(v)
                for tag in tags:
                    if tagdict.has_key(tag):
                        tagdict[tag] = '%s,%s' % (str(postid),tagdict[tag])
                    else:
                        tagdict[tag] = str(postid)
                setkv(k,encode_dict(tagdict))
        else:
            mdb._ensure_connected()
            for tag in tags:
                obj = mdb.get('SELECT * FROM `sp_tags` WHERE `name` = \'%s\' LIMIT 1' % tag)

                if obj:
                    query = "UPDATE `sp_tags` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
                    mdb.execute(query, "%s,"%postid, obj.id)
                else:
                    query = "INSERT INTO `sp_tags` (`name`,`id_num`,`content`) values(%s,1,%s)"
                    mdb.execute(query, tag, postid)

    def remove_postid_from_tags(self, tags = [], postid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if tags and postid:
                k = 'kv_tags'
                v = getkv(k)
                if v:
                    tagdict = decode_dict(v)
                    for tag in tags:
                        tag = tag.encode('utf-8')
                        idlist = tagdict[tag].split(',')
                        if postid in idlist:
                            idlist.remove(postid)
                            try:
                                idlist.remove('')
                            except:
                                pass
                            if len(idlist) == 0:
                                tagdict.pop(tag)
                            else:
                                tagdict[tag] = ','.join(idlist)
                    setkv(k,encode_dict(tagdict))
        else:
            mdb._ensure_connected()
            for tag in tags:
                obj = mdb.get('SELECT * FROM `sp_tags` WHERE `name` = \'%s\' LIMIT 1' % tag)

                if obj:
                    idlist = obj.content.split(',')
                    if postid in idlist:
                        idlist.remove(postid)
                        try:
                            idlist.remove('')
                        except:
                            pass
                        if len(idlist) == 0:
                            mdb.execute("DELETE FROM `sp_tags` WHERE `id` = %s LIMIT 1", obj.id)
                        else:
                            query = "UPDATE `sp_tags` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                            mdb.execute(query, len(idlist), ','.join(idlist), obj.id)
                    else:
                        pass

Tag = Tag()

#yobin 20120629 add begin
class Archive():
    def set_arches(self,names):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_arches'
            setkv(k,str(names))

    def get_latest_archive_name(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_arches'
            v = getkv(k)
            if v:
                ardict = decode_dict(v)
                L = ardict.keys()
                L.sort()
                return L[-1]
            return ''
        else:
            sdb._ensure_connected()
            objs = sdb.query('SELECT `name` FROM `sp_archive` ORDER BY `name` DESC LIMIT 1')
            return objs[0].name

    def get_all_archive_name(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_arches'
            v = getkv(k)
            if v:
                ardict = decode_dict(v)
                arlist = sorted(ardict.keys(),reverse=True)
                return [(item,len(ardict[item].split(','))) for item in arlist]
            return None
        else:
            # [{'id_num': 4, 'name': u'201603'},]
            sdb._ensure_connected()
            return sdb.query('SELECT `name`,`id_num` FROM `sp_archive` ORDER BY `name` DESC')

    def get_archive_by_name(self, name = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name:
                k = 'kv_arches'
                v = getkv(k)
                if v:
                    name = name.encode('utf-8')
                    ardict = decode_dict(v)
                    if name in ardict:
                        return ardict[name]
            return []
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_archive` WHERE `name` = \'%s\' LIMIT 1' % name)

    def get_all_post_num(self, name = ''):
        #这个函数没有调用
        if MYSQL_TO_KVDB_SUPPORT:
            obj = self.get_archive_by_name(name)
            if obj:
                return len(obj.split(','))
            return 0
        else:
            obj = self.get_archive_by_name(name)
            if obj and obj.content:
                return len(obj.content.split(','))
            return 0

    def get_archive_page_posts(self, name = '', page = 1, limit = EACH_PAGE_POST_NUM):
        if MYSQL_TO_KVDB_SUPPORT:
            obj = self.get_archive_by_name(name)
            if obj:
                idlist = obj.split(',')
                page = int(page)
                getids = idlist[limit*(page-1):limit*page]
                return post_list_format(Article.get_related_articles(getids))
            return []
        else:
            obj = self.get_archive_by_name(name)
            if obj:
                page = int(page)
                idlist = obj.content.split(',')
                getids = idlist[limit*(page-1):limit*page]
                sdb._ensure_connected()
                return post_list_format(sdb.query("SELECT * FROM `sp_posts` WHERE `id` in(%s) ORDER BY `id` DESC LIMIT %s" % (','.join(getids), str(len(getids)))))
            return []

    def add_postid_to_archive(self, name = '', postid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name and postid:
                k = 'kv_arches'
                v = getkv(k)
                if v:
                    name = name.encode('utf-8')
                    ardict = decode_dict(v)
                    if ardict.has_key(name):
                        ardict[name] = '%s,%s' % (str(postid),ardict[name])
                    else:
                        ardict[name] = str(postid)
                    setkv(k,encode_dict(ardict))
        else:
            mdb._ensure_connected()
            #因为 UPDATE 时无论有没有影响行数，都返回0，所以这里要多读一次（从主数据库读）
            obj = mdb.get('SELECT * FROM `sp_archive` WHERE `name` = \'%s\' LIMIT 1' % name)

            if obj:
                query = "UPDATE `sp_archive` SET `id_num` = `id_num` + 1, `content` =  concat(%s, `content`) WHERE `id` = %s LIMIT 1"
                mdb.execute(query, "%s,"%postid, obj.id)
            else:
                query = "INSERT INTO `sp_archive` (`name`,`id_num`,`content`) values(%s,1,%s)"
                mdb.execute(query, name, postid)

    def remove_postid_from_archive(self, name = '', postid = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name and postid:
                k = 'kv_arches'
                v = getkv(k)
                if v:
                    name = name.encode('utf-8')
                    ardict = decode_dict(v)
                    if name in ardict:
                        idlist = ardict[name].split(',')
                        idlist.remove(postid)
                        try:
                            idlist.remove('')
                        except:
                            pass
                        if len(idlist) == 0:
                            ardict.pop(name)
                        else:
                            ardict[name] = ','.join(idlist)
                        setkv(k,encode_dict(ardict))
        else:
            mdb._ensure_connected()
            obj = mdb.get('SELECT * FROM `sp_archive` WHERE `name` = \'%s\' LIMIT 1' % name)
            if obj:
                idlist = obj.content.split(',')
                if postid in idlist:
                    idlist.remove(postid)
                    try:
                        idlist.remove('')
                    except:
                        pass
                    if len(idlist) == 0:
                        mdb.execute("DELETE FROM `sp_archive` WHERE `id` = %s LIMIT 1", obj.id)
                    else:
                        query = "UPDATE `sp_archive` SET `id_num` = %s, `content` =  %s WHERE `id` = %s LIMIT 1"
                        mdb.execute(query, len(idlist), ','.join(idlist), obj.id)
                else:
                    pass

Archive = Archive()
#yobin 20120629 add end

#设定暂时仅支持单用户
class User():
    def set_user(self,v):
        if v:
            k = 'kv_user'
            setkv(k,v)

    def check_has_user(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_user'
            v = getkv(k)
            if v:
                return True
            return False
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT `id` FROM `sp_user` LIMIT 1')

    def get_all_user(self):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_user'
            return getkv(k)
        else:
            sdb._ensure_connected()
            return sdb.query('SELECT * FROM `sp_user`')

    def get_user_by_name(self, name):
        if MYSQL_TO_KVDB_SUPPORT:
            k = 'kv_user'
            v = getkv(k)
            if v:
                return decode_dict(v)
            return None
        else:
            sdb._ensure_connected()
            return sdb.get('SELECT * FROM `sp_user` WHERE `name` = \'%s\' LIMIT 1' % str(name))

    def add_new_user(self, name = '', pw = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            return
            if name and pw:
                k = 'kv_user'
                v = getkv(k)
                if v:
                    #设定暂时仅支持单用户，简化程序
                    pass
                else:
                    uinfo = {}
                    #uinfo['id'] = 0
                    uinfo['name'] = name
                    uinfo['password'] = md5(pw.encode('utf-8')).hexdigest()
                    setkv(k,encode_dict(uinfo))
                    return uinfo
        else:
            if name and pw:
                query = "insert into `sp_user` (`name`,`password`) values(%s,%s)"
                mdb._ensure_connected()
                return mdb.execute(query, name, md5(pw.encode('utf-8')).hexdigest())
        return None

    def check_user(self, name = '', pw = ''):
        if MYSQL_TO_KVDB_SUPPORT:
            if name and pw:
                user = self.get_user_by_name(name)
                if user and user['name'] == name and user['password'] == pw:
                    return True
        else:
            if name and pw:
                user = self.get_user_by_name(name)
                if user and user.name == name and user.password == pw:
                    return True
        return False

User = User()

class MyData():
    def flush_all_data(self):
        sql = """
        TRUNCATE TABLE `sp_category`;
        TRUNCATE TABLE `sp_comments`;
        TRUNCATE TABLE `sp_links`;
        TRUNCATE TABLE `sp_posts`;
        TRUNCATE TABLE `sp_tags`;
        TRUNCATE TABLE `sp_archive`;
        TRUNCATE TABLE `sp_user`;
        """
        mdb._ensure_connected()
        mdb.execute(sql)

    def creat_table(self):
        sql = """
DROP TABLE IF EXISTS `sp_category`;
CREATE TABLE IF NOT EXISTS `sp_category` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(17) NOT NULL DEFAULT '',
  `id_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_archive`;
CREATE TABLE IF NOT EXISTS `sp_archive` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(17) NOT NULL DEFAULT '',
  `id_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_comments`;
CREATE TABLE IF NOT EXISTS `sp_comments` (
  `id` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `postid` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `author` varchar(20) NOT NULL,
  `email` varchar(30) NOT NULL,
  `url` varchar(75) NOT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `add_time` int(10) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `postid` (`postid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_links`;
CREATE TABLE IF NOT EXISTS `sp_links` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `displayorder` tinyint(3) NOT NULL DEFAULT '0',
  `name` varchar(100) NOT NULL DEFAULT '',
  `url` varchar(200) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_posts`;
CREATE TABLE IF NOT EXISTS `sp_posts` (
  `id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `category` varchar(17) NOT NULL DEFAULT '',
  `title` varchar(100) NOT NULL DEFAULT '',
  `content` mediumtext NOT NULL,
  `comment_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `closecomment` tinyint(1) NOT NULL DEFAULT '0',
  `tags` varchar(100) NOT NULL,
  `archive` varchar(6) NOT NULL DEFAULT '209901',
  `password` varchar(8) NOT NULL DEFAULT '',
  `add_time` int(10) unsigned NOT NULL DEFAULT '0',
  `edit_time` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `category` (`category`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_tags`;
CREATE TABLE IF NOT EXISTS `sp_tags` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(17) NOT NULL DEFAULT '',
  `id_num` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `content` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `name` (`name`),
  KEY `id_num` (`id_num`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

DROP TABLE IF EXISTS `sp_user`;
CREATE TABLE IF NOT EXISTS `sp_user` (
  `id` smallint(6) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL DEFAULT '',
  `password` varchar(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

"""

        mdb._ensure_connected()
        mdb.execute(sql)

MyData = MyData()
