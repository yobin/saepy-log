# -*- coding: utf8
# Author: twinsant@gmail.com
import hashlib
import xml.etree.ElementTree as ET
from setting import WX_TOKEN
from time import time

class WeiXin(object):
    def __init__(self, token=WX_TOKEN, timestamp=None, nonce=None, signature=None, echostr=None, xml_body=None):
        self.token = token
        self.timestamp = timestamp
        self.nonce = nonce
        self.signature = signature
        self.echostr = echostr

        self.xml_body = xml_body

    @classmethod
    def on_connect(self, token=WX_TOKEN, timestamp=None, nonce=None, signature=None, echostr=None):
        obj = WeiXin(token=token,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature,
            echostr=echostr)
        return obj

    @classmethod
    def on_message(self, xml_body):
        obj = WeiXin(xml_body=xml_body)
        return obj

    def to_json(self):
        '''http://docs.python.org/2/library/xml.etree.elementtree.html#xml.etree.ElementTree.XML
        '''
        j = {}
        root = ET.fromstring(self.xml_body)
        for child in root:
            if child.tag == 'CreateTime':
                value = long(child.text)
            else:
                value = child.text
            j[child.tag] = value
        return j

    def _to_tag(self, k):
        return ''.join([w.capitalize() for w in k.split('_')])

    def _cdata(self, data):
        '''http://stackoverflow.com/questions/174890/how-to-output-cdata-using-elementtree
        '''
        if type(data) is str:
            return '<![CDATA[%s]]>' % data.replace(']]>', ']]]]><![CDATA[>')
        return data

    def to_xml(self, **kwargs):
        xml = '<xml>'
        def cmp(x, y):
            ''' WeiXin need ordered elements?
            '''
            orderd = ['to_user_name', 'from_user_name', 'create_time', 'msg_type', 'content',]# 'func_flag']
            try:
                ix = orderd.index(x)
            except ValueError:
                print 'error 1'
                return 1
            try:
                iy = orderd.index(y)
            except ValueError:
                print 'error 2'
                return -1
            return ix - iy
        for k in sorted(kwargs.iterkeys(), cmp):
            v = kwargs[k]
            tag = self._to_tag(k)
            xml += '<%s>%s</%s>' % (tag, self._cdata(v), tag)
        xml += '</xml>'
        return xml

    def validate(self):
        params = {}
        params['token'] = self.token
        params['timestamp'] = self.timestamp
        params['nonce'] = self.nonce

        signature = self.signature
        # 不需要判断echostr，因为每个POST请求不会发echostr，只有第一次Get请求会发echostr
        # echostr = self.echostr

        if self.is_not_none(params):
            _signature = self._signature(params)
            if _signature == signature:
                return True
        return False

    def is_not_none(self, params):
        for k, v in params.items():
            if v is None:
                return False
        return True

    def _signature(self, params):
        '''http://docs.python.org/2/library/hashlib.html
        '''
        a = sorted([v for k, v in params.items()])
        s = ''.join(a)
        return hashlib.sha1(s).hexdigest()

    # 打包消息xml，作为返回
    def pack_text_xml(self,post_msg,response_msg):
        text_tpl = '''<xml>
                    <ToUserName><![CDATA[%s]]></ToUserName>
                    <FromUserName><![CDATA[%s]]></FromUserName>
                    <CreateTime>%s</CreateTime>
                    <MsgType><![CDATA[%s]]></MsgType>
                    <Content><![CDATA[%s]]></Content>
                    <FuncFlag>0</FuncFlag>
                    </xml>'''
        text_tpl = text_tpl % (str(post_msg['FromUserName']),str(post_msg['ToUserName']),str(int(time())),'text',str(response_msg))
        # 调换发送者和接收者，然后填入需要返回的信息到xml中
        return text_tpl

    #-----------------------------------------------------------------------
    # 打包图文消息xml
    def pack_news_xml(self,post_msg,response_msg):
        articles = ''		# 文章部分
        article_tpl = '''<item>
                     <Title><![CDATA[%s]]></Title>
                     <Description><![CDATA[%s]]></Description>
                     <PicUrl><![CDATA[%s]]></PicUrl>
                     <Url><![CDATA[%s]]></Url>
                     </item>'''
        # 在这里对aticle进行包装
        for i in range(0, len(response_msg['articles']) ):
            articles  += article_tpl % (str(response_msg['articles'][i]['title']),
                                        str(response_msg['articles'][i]['description']),
                                        str(response_msg['articles'][i]['picUrl']),
                                        str(response_msg['articles'][i]['url']))		# 连接

        # 将在article里面插入若干个item
        news_tpl = '''<xml>
                     <ToUserName><![CDATA[%s]]></ToUserName>
                     <FromUserName><![CDATA[%s]]></FromUserName>
                     <CreateTime>%s</CreateTime>
                     <MsgType><![CDATA[%s]]></MsgType>
                     <ArticleCount>%d</ArticleCount>
                     <Articles>
                     %s
                     </Articles>
                     <FuncFlag>1</FuncFlag>
                     </xml>'''
        # 填充内容到xml中
        news_tpl = news_tpl % (post_msg['FromUserName'],post_msg['ToUserName'],
                str(int(time())),'news',len(response_msg['articles']), articles)
        # 调换发送者和接收者，然后填入需要返回的信息到xml中
        return news_tpl

    #-----------------------------------------------------------------------
    # 打包图片消息xml
    def pack_pic_xml(self,post_msg,response_msg):
        img_tpl = '''<xml>
                    <ToUserName><![CDATA[%s]]></ToUserName>
                    <FromUserName><![CDATA[%s]]></FromUserName>
                    <CreateTime>%s</CreateTime>
                    <MsgType><![CDATA[%s]]></MsgType>
                    <Content><![CDATA[%s]]></Content>
                    <FuncFlag>0</FuncFlag>
                    </xml>'''
        img_tpl = img_tpl % (post_msg['FromUserName'],post_msg['ToUserName'],str(int(time())),'image',response_msg)
        # 调换发送者和接收者，然后填入需要返回的信息到xml中
        return img_tpl

    #-----------------------------------------------------------------------
    # 打包声音消息xml
    def pack_music_xml(self,post_msg,response_msg):
       music_tpl = '''<xml>
                   <ToUserName><![CDATA[%s]]></ToUserName>
                   <FromUserName><![CDATA[%s]]></FromUserName>
                   <CreateTime>%s</CreateTime>
                   <MsgType><![CDATA[%s]]></MsgType>
                   <Music>
                   <Title><![CDATA[%s]]></Title>
                   <Description><![CDATA[%s]]></Description>
                   <MusicUrl><![CDATA[%s]]></MusicUrl>
                   <HQMusicUrl><![CDATA[%s]]></HQMusicUrl>
                   </Music>
                   <FuncFlag>0</FuncFlag>
                   </xml>'''
       music_tpl = music_tpl % (post_msg['FromUserName'],post_msg['ToUserName'],str(int(time())),'music',response_msg)
       # 调换发送者和接收者，然后填入需要返回的信息到xml中
       return music_tpl
