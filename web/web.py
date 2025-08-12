
# Python System
from pprint import pprint
import os, sys
import json

import logging

try:
    # External Modules
    from flask import Flask
    from flask import request
    from flask import send_file
    from flask import redirect
    from flask import make_response
    from flask import send_from_directory
except Exception as e:
        print("Need to install Python module [flask]")
        sys.exit(1)

from multiprocessing import Process

# Internal Modules
from handler.mediareader import MediaReader


class WebInterface(object):
    """Web interface for managing rips

    """

    def __init__(self,settings=None):


        self.host_dir=os.path.realpath(__file__).replace(os.path.basename(__file__),"")

        self.app = Flask("PyDiscRip")
        self.app.logger.disabled = True
        #log = logging.getLogger('werkzeug')
        #log.disabled = True

        # Static content
        self.app.static_folder=self.host_dir+"http/static"
        self.app.static_url_path='/static/'
        # Define routes in class to use with flask
        self.app.add_url_rule('/','home', self.index)
        self.app.add_url_rule('/settings.json','settings_json', self.settings_json)
        self.app.add_url_rule('/config_data.json','config_data_json', self.config_data_json)
        self.app.add_url_rule('/rip','rip', self.web_rip,methods=["POST"])
        self.app.add_url_rule('/output/<path:name>','rip_data', self.web_rip_data)
        self.app.add_url_rule('/status/status.json','output_status_json', self.output_status_json)
        self.app.add_url_rule('/status/drive_status.json','drive_status_json', self.drive_status_json)
        self.app.add_url_rule('/status/queue.json','queue_json', self.queue_json)
        self.app.add_url_rule('/status/file','settings_json', self.settings_json)
        self.app.add_url_rule('/update','update', self.update,methods=["POST"])

        # Callback data
        self.drive_status={}
        self.queue=[]

        # Set headers for server
        self.app.after_request(self.add_header)

        if settings is not None:
            self.settings=settings
            self.host = settings["web"]["ip"]
            self.port = settings["web"]["port"]



    def set_host(self,host_ip):
        self.host = host_ip

    def set_port(self,host_port):
        self.port = host_port


    def add_header(self,r):
        """
        Force the page cache to be reloaded each time
        """
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    def static_files(self,name):
        print(f"static: {name}")
        return send_from_directory(self.host_dir+"http/static", name)


    def index(self):
        """ Simple class function to send HTML to browser """
        return send_file(self.host_dir+"http/home.html")

    def settings_json(self):
        """ Simple class function to send HTML to browser """
        return json.dumps(self.settings), 200, {'Content-Type': 'application/json; charset=utf-8'}

    def config_data_json(self):
        """ Simple class function to send HTML to browser """
        return json.dumps(MediaReader.getConfigOptions()), 200, {'Content-Type': 'application/json; charset=utf-8'}

    def web_rip(self):
        """ Simple class function to send HTML to browser """
        pprint(request.form.to_dict())

        media_sample={}
        media_sample["name"] = request.form['media_name']
        media_sample["media_type"] = request.form['media_type']
        if(MediaReader.isGroup(self.settings["drives"],request.form['media_drive'])):
            media_sample["group"] = request.form['media_drive']
        else:
            media_sample["drive"] = request.form['media_drive']
        media_sample["description"] = request.form['media_description']
        media_sample["config_data"] = json.loads(request.form['config_options_json_data'])
        #return pprint(request.form)

        with open(f"{self.settings["watch"]}/{media_sample["name"]}.json", 'w', encoding="utf-8") as output:
            output.write(json.dumps(media_sample, indent=4))

        # self.rip_thread = Process(target=MediaReader.rip,kwargs={"media_sample":media_sample,"config_data":{},"callback_update":self.media_sample_status})
        # self.rip_thread.start()
        #return pprint(request.form)
        return send_file(self.host_dir+"http/rip/index.html")

    def update(self):
        """ Simple class function to send HTML to browser """

        print("Updating API")
        pprint(request.form.to_dict())
        data_dict = request.form.to_dict()
        if not data_dict:
            pprint(request.get_data())
            data = json.loads(request.get_data())
        else:
            data = json.loads(next(iter(data_dict)))
        pprint(data)

        if "drive_status" in data:
            print("Updating drive status")
            for drive, update in data["drive_status"].items():
                if drive not in self.drive_status:
                    self.drive_status[drive]={}
                for key, value in update.items():
                    self.drive_status[drive][key] = value


        if "queue" in data:
            # support list or not
            if not isinstance(data["queue"], list):
                data["queue"] = [data["queue"]]
            for media_sample in data["queue"]:
                media_sample.pop('config_data', None)
                media_sample.pop('settings', None)
                match = next((i for i, item in enumerate(self.queue) if item["name"] == media_sample["name"]), None)
                if match is not None:
                    self.queue[match] = media_sample
                else:
                    self.queue.append(media_sample)



        return "thx"

    def media_sample_status(self,media_sample):
        filepath=media_sample["name"]+"/media_sample.json"
        print(f"writing: {filepath}")
        # Write data
        with open(filepath, 'w', encoding="utf-8") as output:
            output.write(json.dumps(media_sample, indent=4))

    def web_rip_data(self,name):
        print(f"web_rip_data: {name}")
        return send_file(f"{name}")

    def output_status_json(self):
        done = request.args.get('done')=="true"
        outputs=[]
        names=None
        if (request.args.get('names') is not None):
            names=json.dumps(request.args.get('names'))

        for root, dirs, files in os.walk(self.settings["output"]):
            for output in dirs:

                if os.path.exists(f"{self.settings["output"]}/{output}/status/status.json"):

                    with open(f"{self.settings["output"]}/{output}/status/status.json", newline='') as jsonfile:
                        status = json.load(jsonfile)
                        # Filter by status
                        if request.args.get('done') is not None and status["done"] != done:
                            continue
                        # Filter by name
                        if names is not None and status["name"] not in names:
                            continue

                        outputs.append(status)

            return json.dumps(outputs), 200, {'Content-Type': 'application/json; charset=utf-8'}
        return ""

    def drive_status_json(self):
        """ Simple class function to send HTML to browser """
        return json.dumps(self.drive_status), 200, {'Content-Type': 'application/json; charset=utf-8'}

    def queue_json(self):
        """ Simple class function to send HTML to browser """
        return json.dumps(self.queue), 200, {'Content-Type': 'application/json; charset=utf-8'}

    def callback_update(self,data):
        if "drive_status" in data:
            print("Updating drive status")
            pprint(data["drive_status"])
            self.drive_status = data["drive_status"]

        return None


    async def start(self):
        """ Run Flask in a process thread that is non-blocking """
        print("Starting Flask")
        self.web_thread = Process(target=self.app.run,
            kwargs={
                "host":self.host,
                "port":self.port,
                "debug":True,
                "use_reloader":False
                }
            )
        self.web_thread.start()

        # Pass settings
        config_data={}
        config_data["settings"] = self.settings

        self.rip_thread = Process(target=MediaReader.rip_queue_groups,
            kwargs={
                "media_samples":[],
                "config_data":config_data,
                "callback_update":self.callback_update
                }
            )
        self.rip_thread.start()

    def stop(self):
        """ Send SIGKILL and join thread to end Flask server """
        if hasattr(self, "web_thread") and self.web_thread is not None:
            self.web_thread.terminate()
            self.web_thread.join()
        if hasattr(self, "rip_thread"):
            self.rip_thread.terminate()
            self.rip_thread.join()
