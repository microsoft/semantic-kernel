# To be used to test GoogleCredentials.get_application_default()
# from devel GAE (ie, dev_appserver.py).

from googleapiclient.discovery import build
import webapp2

from oauth2client.client import GoogleCredentials


PROJECT = 'bamboo-machine-422'  # Provide your own GCE project here
ZONE = 'us-central1-a'          # Put here a zone which has some VMs


def get_instances():
    credentials = GoogleCredentials.get_application_default()
    service = build('compute', 'v1', credentials=credentials)
    request = service.instances().list(project=PROJECT, zone=ZONE)
    return request.execute()


class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.write(get_instances())


app = webapp2.WSGIApplication([('/', MainPage), ], debug=True)
