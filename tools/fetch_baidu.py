#!/usr/bin/python
#coding:utf8
#Author = yyobin@gmail.com
#Create = 20120517

import cookielib, urllib2, urllib
import os,sys,socket,re
import datetime,time
import HTMLParser

blog = "http://hi.baidu.com/new/*****" #你自己的百度博客链接，需要修改
baidu_user   = ''                #你的百度登录名,暂未考虑中文ID，比如abc
baidu_psw    = ''                  #你的百度登陆密码,如果不输入用户名和密码，就没发获取私有的文章

movesecret   = '123456'      #迁移新博客的需要密码，你总不能希望有人找到这个后门给你发表一大堆垃圾文章吧
privatepsw   = ''                  #新博客私有文章的密码，自己设置，不设置也行
moveurl      = 'http://****.sinaapp.com/admin/moveblog'  #新博客对应的迁移入口，需要修改

#解析有多少页博客
#pageStr = """var PagerInfo = {allCount : '(\d+)',pageSize : '(\d+)','''#curPage : '\d+'};"""
pageStr = """allCount : '(\d+)',.*?pageSize : '(\d+)',"""
pageObj = re.compile(pageStr, re.DOTALL)


#获取登陆token
login_tokenStr = '''bdPass.api.params.login_token='(.*?)';'''
login_tokenObj = re.compile(login_tokenStr,re.DOTALL)

#获取博客标题和url
blogStr = r'''<div class="hide q-username"><a href=".*?" class=a-normal target=_blank>.*?</a></div><a href="(.*?)" class="a-incontent a-title" target=_blank>(.*?)</a></div><div class=item-content>'''
blogObj = re.compile(blogStr,re.DOTALL)

#解析博客内容
ConStr  = '''<div class=content-other-info> <span>(\d+)-(\d+)-(\d+) (\d+):(\d+).*?<h2 class="title content-title">(.*?)</h2>.*?<div id=content class="content text-content clearfix">(.*?)</div>.*?<a class=tag href=".*?">#(.*?)</a>.*?<span class=pv>.*?(\d+)\)</span>'''
ConObj  = re.compile(ConStr,re.DOTALL)

class Baidu(object):
    def __init__(self,user = '', psw = '', blog = ''):
        self.user    = user#暂未考虑中文ID
        self.psw     = psw
        self.blog    = blog
        self.urls    = []
        self.succeed = 0

        if not user or not psw or not blog:
            print "Plz enter enter 3 params:user,psw,blog"
            sys.exit(0)

        self.cookiename = 'baidu%s.coockie' % (self.user)
        self.token = ''

        self.allCount  = 0
        self.pageSize  = 10
        self.totalpage = 0

        self.logined = False
        self.cj = cookielib.LWPCookieJar()
        try:
            self.cj.revert(self.cookiename)
            self.logined = True
            print "Login OK"
        except Exception,e:
            print e

        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders = [('User-agent','Opera/9.23')]
        urllib2.install_opener(self.opener)

        socket.setdefaulttimeout(30)

    def get_url_data(self,url):
        nFail = 0
        while nFail < 1:#就怕多传了，服务器也接收blog了
            try:
                rsp = self.opener.open(url).read()
                return rsp
            except:
                nFail += 1
                print "get url fail:%s count=%d" % (url,nFail)
        print "get url fail:%s" % (url)
        return ''

    #登陆百度
    def login(self):
        #如果没有获取到cookie，就模拟登陆一下
        if not self.logined:
            print "need logon"
            #第一次访问一下，目的是为了先保存一个cookie下来
            qurl = '''https://passport.baidu.com/v2/api/?getapi&class=login&tpl=mn&tangram=false'''
            r = self.opener.open(qurl)
            self.cj.save(self.cookiename)

            #第二次访问，目的是为了获取token
            qurl = '''https://passport.baidu.com/v2/api/?getapi&class=login&tpl=mn&tangram=false'''
            r = self.opener.open(qurl)
            rsp = r.read()
            self.cj.save(self.cookiename)

            #通过正则表达式获取token
            matched_objs = login_tokenObj.findall(rsp)
            if matched_objs:
                self.token = matched_objs[0]
                print 'Token = %s' % (str(self.token))
                #然后用token模拟登陆
                post_data = urllib.urlencode({'username':self.user,
                                              'password':self.psw,
                                              'token':self.token,
                                              'charset':'UTF-8',
                                              'callback':'parent.bd12Pass.api.login._postCallback',
                                              'index':'0',
                                              'isPhone':'false',
                                              'mem_pass':'on',
                                              'loginType':'1',
                                              'safeflg':'0',
                                              'staticpage':'https://passport.baidu.com/v2Jump.html',
                                              'tpl':'mn',
                                              'u':'http://www.baidu.com/',
                                              'verifycode':'',
                                            })
                #path = 'http://passport.baidu.com/?login'
                path = 'http://passport.baidu.com/v2/api/?login'
                self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
                self.opener.addheaders = [('User-agent','Opera/9.23')]
                urllib2.install_opener(self.opener)
                headers = {
                  "Accept": "image/gif, */*",
                  "Referer": "https://passport.baidu.com/v2/?login&tpl=mn&u=http%3A%2F%2Fwww.baidu.com%2F",
                  "Accept-Language": "zh-cn",
                  "Content-Type": "application/x-www-form-urlencoded",
                  "Accept-Encoding": "gzip, deflate",
                  "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)",
                  "Host": "passport.baidu.com",
                  "Connection": "Keep-Alive",
                  "Cache-Control": "no-cache"
                }
                req = urllib2.Request(path,
                                post_data,
                                headers=headers,
                                )
                rsp = self.opener.open(req).read()
                #如果觉得有必要的话，在这里自己读一下rsp判断一下是否登陆OK，我打印过登陆没问题
                self.cj.save(self.cookiename)
            else:
                print "Login Fail"
                sys.exit(0)

    #获取博客一共有多少页，如果有私有博客的话，登陆和不登陆获取的是不一样的
    def getTotalPage(self):
        #获取博客的总页数
        rsp = self.opener.open(self.blog).read()

        if rsp:
            #print rsp
            #rsp = rsp.replace('\r','').replace('\n','').replace('\t','')
            matched_objs = pageObj.findall(rsp)
            if matched_objs:
                obj0,obj1 = matched_objs[0]
                #print obj0,obj1
                self.allCount = int(obj0)
                self.pageSize = int(obj1)
                self.totalpage = (self.allCount / self.pageSize) + 1
                print self.allCount,self.pageSize,self.totalpage

    #获取每一页里的博客链接
    def fetchPage(self,url,flag):
        rsp = self.get_url_data(url)
        if rsp:
            rsp = rsp.replace('\r','').replace('\n','').replace('\t','')
            matched_objs = blogObj.findall(rsp)
            if matched_objs:
                for obj in matched_objs:
                    url   = obj[0]
                    title = obj[1]
                    if flag == 'download':
                        #这里可以用多线程改写一下,单线程太慢，不过一般人也没那么多博客，我的两千多篇博客迁移的时间也不长。
                        self.download(url,title)
                    elif flag == 'move':
                        self.urls.append(url)
                        #self.move(url,title)
                    else:
                        print 'flag err.'
                return
        print 'fetchPage err. url = %s' % (url)
                    #break

    #迁移博客到SAE上
    def move(self,url):
        url = 'http://hi.baidu.com%s' % (url)
        rsp = self.get_url_data(url)
        if rsp:
            if 'private4host' in rsp:
                private = privatepsw
            else:
                private = ''
            matched_objs = ConObj.findall(rsp)
            if matched_objs:
                year  = int(matched_objs[0][0])
                mon   = int(matched_objs[0][1])
                day   = int(matched_objs[0][2])
                hour  = int(matched_objs[0][3])
                min   = int(matched_objs[0][4])
                title = matched_objs[0][5]
                con   = matched_objs[0][6]
                cat   = matched_objs[0][7].replace('python &#38; django &#38; gae','python').replace('python &#38; django','python')#对我博客的特殊处理
                pv    = matched_objs[0][8]
                dt    = int(time.mktime(datetime.datetime(year,mon,day,hour,min,0).timetuple()))
                post_data = urllib.urlencode({'s':movesecret,
                                              'cat':cat,
                                              'tag':cat,
                                              'tit':title,
                                              'con':con,
                                              'addtime':dt,
                                              'edit_time':dt,
                                              'archive':'%s%2s' % (str(matched_objs[0][0]),str(matched_objs[0][1])),
                                              'p': private,
                                              'pv':pv
                                            })
                urllib2.install_opener(self.opener)
                headers = {
                  "Accept": "image/gif, */*",
                  "Accept-Language": "zh-cn",
                  "Content-Type": "application/x-www-form-urlencoded",
                  "Accept-Encoding": "gzip, deflate",
                  "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)",
                  "Connection": "Keep-Alive",
                  "Cache-Control": "no-cache"
                }
                req = urllib2.Request(moveurl,
                                post_data,
                                headers=headers,
                                )
                rsp = self.get_url_data(req)
                if '''"status": 200''' in rsp:
                    self.succeed += 1
                    print self.succeed
                    return True
                else:
                    print url
                    return False
        else:
            print 'fail to move url:%s' % (url)
            return False

    def downloadBywinget(self,url,title):
        pass#比如使用wget之类的第三方工具，自己填参数写

    #下载博客
    def download(self,url,title):
        titles = []
        if title in titles:
            title = '%s_new' % (title)
        titles.append(title)
        path = '%s/%s.html' % (self.user,url.replace('/%s/item/' % (baidu_user),''))
        url = 'http://hi.baidu.com%s' % (url)
        print "Download url %s" % (url)

        nFail = 0
        while nFail < 5:
            try:
                rsp = self.get_url_data(url)
                myfile = file(path,'w')
                myfile.write(rsp)
                myfile.close()
                return
            except:
                nFail += 1
        print 'download blog fail:%s' % (url)

    def handledall(self,flag = 'download'):
        if flag == 'move':
            if not os.path.exists(self.user):
                os.mkdir(self.user)#下载放着博客时的目录
        for page in range(1,self.totalpage+1):
            url = "%s?page=%d" % (self.blog,page)
            #这里可以用多线程改写一下,单线程太慢
            self.fetchPage(url,flag)
        if flag == 'move':
            print '============================================'
            print self.urls
            print '============================================'
            for url in list(reversed(self.urls)):
                if not self.move(url):
                    return#在这里return是为了后续看从哪里接着传

    def slugfy(self,text, separator='-'):
        text = text.lower()
        text = re.sub('[¿_\-　，。：；‘“’”【】『』§！－——＋◎＃￥％……※×（）《》？、÷<>/\|:"*?]+', ' ', text)
        ret_list = []
        for c in text:
            ordnum = ord(c)
            if 47<ordnum<58 or 96<ordnum<123:
                ret_list.append(c)
            else:
                if re.search(u"[\u4e00-\u9fa5]", c):
                    ret_list.append(c)
                else:
                    ret_list.append(' ')
        ret = ''.join(ret_list)
        ret = re.sub(r"\ba\b|\ban\b|\bthe\b", '', ret)
        ret = ret.strip()
        ret = re.sub("[\s]+", separator, ret)

        ret = HTMLParser.HTMLParser().unescape(ret)
        return ret

def main():
    baidu = Baidu(baidu_user,baidu_psw,blog)
    baidu.login()
    baidu.getTotalPage()
    baidu.handledall('move')
    print 'Total blog = %d, handle blog = %d' % (baidu.allCount,baidu.succeed)
    print 'Finish.'

if __name__ == '__main__':
    main()
