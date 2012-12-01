import sae
import tornado.wsgi

from blog import urls as blogurls
from admin import urls as adminurls

#cookie_secret,自己修改一下
settings = { 
    'debug': True,
    "cookie_secret": "SDFAFsdfsf90sa242asdfjnds3HUHY=",
    "login_url": "/login",
    #'gzip': True,    
}

saeurls = blogurls + adminurls

app = tornado.wsgi.WSGIApplication(saeurls, **settings)

application = sae.create_wsgi_app(app)
