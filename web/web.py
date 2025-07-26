
# Python System
from pprint import pprint
import os

# External Modules
from flask import Flask
from flask import request
from flask import send_file
from flask import redirect
from flask import make_response
import logging

from multiprocessing import Process

# Internal Modules
from handler.mediareader import MediaReader


class WebInterface(object):
    """Web interface for managing rips

    """

    def __init__(self):

        self.app = Flask("PyDiscRip")
        self.app.logger.disabled = True
        #log = logging.getLogger('werkzeug')
        #log.disabled = True

        # Define routes in class to use with flask
        self.app.add_url_rule('/','home', self.index)
        self.app.add_url_rule('/rip','rip', self.web_rip,methods=["POST"])

        # Set headers for server
        self.app.after_request(self.add_header)

        self.host = "0.0.0.0"

        self.host_dir=os.path.realpath(__file__).replace(os.path.basename(__file__),"")


    def set_host(self,host_ip):
        self.host = host_ip


    def add_header(self,r):
        """
        Force the page cache to be reloaded each time
        """
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    def index(self):
        """ Simple class function to send HTML to browser """
        return send_file(self.host_dir+"http/home.html")

    def web_rip(self):
        """ Simple class function to send HTML to browser """
        media_sample={}
        media_sample["name"] = request.form['media_name']
        media_sample["media_type"] = request.form['media_type']
        media_sample["drive"] = request.form['media_drive']
        media_sample["description"] = request.form['media_description']

        self.rip_thread = Process(target=MediaReader.rip,kwargs={"media_sample":media_sample,"config_data":{}})
        self.rip_thread.start()
        return "ripping"


    async def start(self):
        """ Run Flask in a process thread that is non-blocking """
        print("Starting Flask")
        self.web_thread = Process(target=self.app.run, kwargs={"host":self.host,"port":5001,"debug":True})
        self.web_thread.start()

    def stop(self):
        """ Send SIGKILL and join thread to end Flask server """
        if hasattr(self, "web_thread") and self.web_thread is not None:
            self.web_thread.terminate()
            self.web_thread.join()
        if hasattr(self, "rip_thread"):
            self.rip_thread.terminate()
            self.rip_thread.join()
