import os
import tornado.httpserver
import tornado.ioloop
import tornado.web
from creds import *
from requests import Request
import requests
import json
import re
import tempfile
import redis
import uuid
from pydub import AudioSegment

	
def gettoken(uid):
	red = redis.from_url(redis_url)
	token = red.get(uid+"-access_token")
	refresh = red.get(uid+"-refresh_token")
	if token:
		return token
	elif refresh:
		payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		resp = json.loads(r.text)
		red.set(uid+"-access_token", resp['access_token'])
		red.expire(uid+"-access_token", 3600)
		return resp['access_token']
	else:
		return False
	
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_cookie("user")


class MainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	def get(self):
		f = open('static/index.html', 'r')
		resp = f.read()
		f.close()
		self.write(resp)
		self.finish()


class StartAuthHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		scope="alexa_all"
		sd = json.dumps({
		    "alexa:all": {
		        "productID": Product_ID,
		        "productInstanceAttributes": {
		            "deviceSerialNumber": "1"
		        }
		    }
		})
		url = "https://www.amazon.com/ap/oa"
		path = self.request.protocol + "://" + self.request.host 
		callback = path + "/code"
		payload = {"client_id" : Client_ID, "scope" : "alexa:all", "scope_data" : sd, "response_type" : "code", "redirect_uri" : callback }
		req = Request('GET', url, params=payload)
		p = req.prepare()
		self.redirect(p.url)


class CodeAuthHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		code=self.get_argument("code")
		path = self.request.protocol + "://" + self.request.host 
		callback = path+"/code"
		payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "code" : code, "grant_type" : "authorization_code", "redirect_uri" : callback }
		url = "https://api.amazon.com/auth/o2/token"
		r = requests.post(url, data = payload)
		uid = str(uuid.uuid4())
		red = redis.from_url(redis_url)
		resp = json.loads(r.text)
		red.set(uid+"-access_token", resp['access_token'])
		red.expire(uid+"-access_token", 3600)
		red.set(uid+"-refresh_token", resp['refresh_token'])
		self.set_cookie("user", uid)
		self.redirect("/")					

class LogoutHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	def get(self):
		uid = tornado.escape.xhtml_escape(self.current_user)
		red = redis.from_url(redis_url)
		red.delete(uid+"-access_token")
		red.delete(uid+"-refresh_token")
		self.clear_cookie("user")
		self.set_header('Content-Type', 'text/plain')
		self.write("Logged Out, Goodbye")
		self.finish()
				
class AudioHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	def post(self):
		uid = tornado.escape.xhtml_escape(self.current_user)
		token = gettoken(uid)
		if (token == False):
			self.set_status(403)
		else:
			rxfile = self.request.files['data'][0]['body']
			tf = tempfile.NamedTemporaryFile(suffix=".wav")
			tf.write(rxfile)
			_input = AudioSegment.from_wav(tf.name)
			tf.close()
			tf = tempfile.NamedTemporaryFile(suffix=".wav")
			output = _input.set_channels(1).set_frame_rate(16000)
			f = output.export(tf.name, format="wav")
			url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
			headers = {'Authorization' : 'Bearer %s' % token}
			d = {
		    	"messageHeader": {
		        	"deviceContext": [
		            	{
		                	"name": "playbackState",
		                	"namespace": "AudioPlayer",
		                	"payload": {
		                    	"streamId": "",
		         			   	"offsetInMilliseconds": "0",
		                    	"playerActivity": "IDLE"
		                	}
		            	}
		        	]
		    	},
		    	"messageBody": {
		        	"profile": "alexa-close-talk",
		        	"locale": "en-us",
		        	"format": "audio/L16; rate=16000; channels=1"
		    	}
			}
			files = [
				('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
				('file', ('audio', tf, 'audio/L16; rate=16000; channels=1'))
			]	
			r = requests.post(url, headers=headers, files=files)
			tf.close()
			for v in r.headers['content-type'].split(";"):
				if re.match('.*boundary.*', v):
					boundary =  v.split("=")[1]
			data = r.content.split(boundary)
			for d in data:
				if (len(d) >= 1024):
			 	   audio = d.split('\r\n\r\n')[1].rstrip('--')
			self.set_header('Content-Type', 'audio/mpeg')
			self.write(audio)
		self.finish()




def main():
	settings = {
	    "cookie_secret": "parisPOLANDbroadFENCEcornWOULD",
	    "login_url": "/static/welcome.html",
	}
	static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
	application = tornado.web.Application([(r"/", MainHandler),
											(r"/start", StartAuthHandler),
											(r"/code", CodeAuthHandler),
											(r"/logout", LogoutHandler),
											(r"/audio", AudioHandler),
											(r'/(favicon.ico)', tornado.web.StaticFileHandler,{'path': static_path}),
											(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': static_path}),
											], **settings)
	http_server = tornado.httpserver.HTTPServer(application)
	port = int(os.environ.get("PORT", 5000))
	http_server.listen(port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
	
	

