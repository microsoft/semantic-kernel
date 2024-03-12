# To be used to test GoogleCredentials.get_application_default()
# from local machine and GCE.
# The GCE virtual machine needs to have both service account and
# Compute API enabled.
# See:  https://developers.google.com/compute/docs/authentication

from googleapiclient.discovery import build

from oauth2client.client import GoogleCredentials


PROJECT = 'bamboo-machine-422'  # Provide your own GCE project here
ZONE = 'us-central1-a'          # Put here a zone which has some VMs


credentials = GoogleCredentials.get_application_default()
service = build('compute', 'v1', credentials=credentials)

request = service.instances().list(project=PROJECT, zone=ZONE)
response = request.execute()

print(response)
