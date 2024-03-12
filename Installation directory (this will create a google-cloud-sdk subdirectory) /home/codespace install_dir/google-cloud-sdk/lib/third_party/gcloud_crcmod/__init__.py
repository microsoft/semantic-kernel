import sys

if sys.version_info < (3,):
  from gcloud_crcmod.python2.crcmod import *
  from gcloud_crcmod.python2 import predefined
else:
  from gcloud_crcmod.python3.crcmod import *
  from gcloud_crcmod.python3 import predefined
