#coding=utf-8
#author : yobin
#date 20160404

import cookielib, urllib2, urllib
import re

def get_url_data(url):
    nFail = 0
    while nFail < 5:
        try:
            sock = urllib.urlopen(url)
            htmlSource = sock.read()
            sock.close()
            return htmlSource
        except:
            nFail += 1
            print "get url fail:%s count=%d" % (url,nFail)
    print "get url fail:%s" % (url)
    return None

def post_url_data(url = '',data = {}):
    if url and data:
        post_data = urllib.urlencode(data)
        req = urllib2.urlopen(url, post_data)
        return req.read()
    return None

def encode_dict(my_dict):
    newdict = {}
    for k in my_dict:
        #newdict[str(k)] = str(my_dict[k]).encode('utf-8')
        newdict[str(k)] = my_dict[k].encode('utf-8') if isinstance(my_dict[k], unicode) else str(my_dict[k])
    return "#@$".join("%s+=-%s" % x for x in newdict.iteritems())

def decode_dict(my_string):
    return dict(x.split("+=-") for x in my_string.split("#@$"))

# 编码list
def encode_list(my_list):
    return "\x1e".join(str(x) for x in my_list)

# 解码list
def decode_list(my_string):
    return list(my_string.split("\x1e"))

# 编码list
def encode_dictlist(my_list):
    return "*@#".join(encode_dict(x) for x in my_list)

# 解码list
def decode_dictlist(my_string):
    tmplist = []
    for item in my_string.split("*@#"):
        tmplist.append(decode_dict(item))
    return tmplist


SEC_CODE = '123456' #与SAE后台设置的一致
tags_str = '''id: (\d+)\s+name: (.*?)\s+id_num: (\d+)\s+content: (.*)'''
tags_obj = re.compile(tags_str)
def parseTag():
    with open('sp_tags.yml','r') as f:
        txt = f.read()
        objs = tags_obj.findall(txt)
        tagdict = {}
        for obj in objs:
            tagdict[obj[1]] = obj[3]
        url = 'http://yobin.sinaapp.com/admin/kv/settags/%s/' % (SEC_CODE)
        data = {'tags':encode_dict(tagdict)}
        rsp = post_url_data(url,data)
        print rsp

def parseCat():
    with open('sp_category.yml','r') as f:
        txt = f.read()
        objs = tags_obj.findall(txt)
        tagdict = {}
        for obj in objs:
            tagdict[obj[1]] = obj[3]
        url = 'http://yobin.sinaapp.com/admin/kv/setcats/%s/' % (SEC_CODE)
        print url
        data = {'cats':encode_dict(tagdict)}
        rsp = post_url_data(url,data)
        print rsp

def parseArch():
    with open('sp_archive.yml','r') as f:
        txt = f.read()
        objs = tags_obj.findall(txt)
        tagdict = {}
        for obj in objs:
            tagdict[obj[1]] = obj[3]
        url = 'http://yobin.sinaapp.com/admin/kv/setarches/%s/' % (SEC_CODE)
        print url
        data = {'arches':encode_dict(tagdict)}
        rsp = post_url_data(url,data)
        print rsp

comment_str = u'''id: (\d+)\s+postid: (\d+)\s+author: (.*?)\s+email: (.*?)\s+url: (.*?)\s+visible: (\d+)\s+add_time: (\d+)\s+content: (.*?)\s+[-.]'''
comment_obj = re.compile(comment_str,re.DOTALL)
def parseComment():
    with open('sp_comments.yml','r') as f:
        txt = f.read()
        objs = comment_obj.findall(txt)
        cdict = {}
        clist = []
        pcdict = {}

        for obj in objs:
            clist.append(obj[0])
            if pcdict.has_key(obj[1]):
                pcdict[obj[1]] = '%s,%s' % (pcdict[obj[1]],obj[0])
            else:
                pcdict[obj[1]] = obj[0]
            url = 'http://yobin.sinaapp.com/admin/kv/setcomment/%s/%s/' % (SEC_CODE,obj[0])
            print url
            cdict = {}
            cdict['id']       = obj[0]
            cdict['postid']   = obj[1]
            cdict['author']   = obj[2]
            cdict['email']    = obj[3]
            cdict['url']      = obj[4]
            cdict['visible']  = obj[5]
            cdict['add_time'] = obj[6]
            if '|-' == obj[7][:2]:
                txt = obj[7][3:]
                txt = txt.replace('    ','')
                cdict['content']    = txt
            else:
                cdict['content']  = obj[7]
            data = {'comment':encode_dict(cdict)}
            rsp = post_url_data(url,data)
            print rsp
        url = 'http://yobin.sinaapp.com/admin/kv/setcomments/%s/' % (SEC_CODE)
        print url
        data = {'comments':','.join(clist)}
        rsp = post_url_data(url,data)
        print rsp

        url = 'http://yobin.sinaapp.com/admin/kv/setpcomm/%s/' % (SEC_CODE)
        print url
        data = {'pcomm':encode_dict(pcdict)}
        rsp = post_url_data(url,data)
        print rsp

post_str = u'''id: (\d+)\s+category: (.*?)\s+title: (.*?)\s+content: (.*?)\s+comment_num: (\d+)\s+closecomment: (\d+)\s+tags: (.*?)\s+archive: (\d+)\s+password: (.*?)\s+add_time: (\d+)\s+edit_time: (\d+)\s+[-.]'''
post_obj = re.compile(post_str,re.DOTALL)
def parsePosts():
    with open('sp_posts.yml','r') as f:
        txt = f.read()
        objs = post_obj.findall(txt)
        cdict = {}
        clist = []

        for obj in objs:
            clist.append(obj[0])

            url = 'http://yobin.sinaapp.com/admin/kv/setarticle/%s/%s/' % (SEC_CODE,obj[0])
            print url
            cdict = {}
            cdict['id']       = obj[0]
            cdict['category']   = obj[1]
            cdict['title']   = obj[2]
            if '|-' == obj[3][:2]:
                txt = obj[3][3:]
                txt = txt.replace('    ','')
                cdict['content']    = txt
            else:
                cdict['content']    = obj[3]
            cdict['comment_num']      = obj[4]
            cdict['closecomment']  = obj[5]
            cdict['tags'] = obj[6]
            cdict['archive']  = obj[7]
            cdict['password']  = obj[8]
            cdict['add_time']  = obj[9]
            cdict['edit_time']  = obj[10]
            data = {'article':encode_dict(cdict)}
            rsp = post_url_data(url,data)
            print rsp
        url = 'http://yobin.sinaapp.com/admin/kv/setarticles/%s/' % (SEC_CODE)
        print url
        clist.sort(lambda x,y:cmp(int(x),int(y)))
        data = {'articles':','.join(clist)}
        rsp = post_url_data(url,data)
        print rsp

user_str = u'''id: (\d+)\s+name: (.*?)\s+password: (.*)'''
user_obj = re.compile(user_str)
def parseUsr():
    with open('sp_user.yml','r') as f:
        txt = f.read()
        objs = user_obj.findall(txt)
        for obj in objs:
            print obj
            url = 'http://yobin.sinaapp.com/admin/kv/setuser/%s/' % (SEC_CODE)
            print url
            cdict = {}
            cdict['name']       = obj[1]
            cdict['password']   = obj[2]
            data = {'data':encode_dict(cdict)}
            rsp = post_url_data(url,data)
            print rsp
            return # Only one user

links_str = u'''id: (\d+)\s+displayorder: (\d+)\s+name: (.*?)\s+url: (.*)'''
links_obj = re.compile(links_str)
def parseLink():
    with open('sp_links.yml','r') as f:
        txt = f.read()
        objs = links_obj.findall(txt)
        dictlist = []
        for obj in objs:
            cdict = {}
            cdict['id']           = obj[0]
            cdict['displayorder'] = obj[1]
            cdict['name']         = obj[2]
            cdict['url']          = obj[3]
            dictlist.append(cdict)
        url = 'http://yobin.sinaapp.com/admin/kv/setlink/%s/' % (SEC_CODE)
        print url
        data = {'data':encode_dictlist(dictlist)}
        rsp = post_url_data(url,data)
        print rsp

def main():
    parseTag()
    parseCat()
    parseArch()
    parseComment()
    parsePosts()
    parseUsr()
    parseLink()


if __name__ == "__main__":
    main()

