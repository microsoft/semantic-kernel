# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
x=sys.modules['containerregistry.client.v1']
  

from containerregistry.client.v1 import docker_creds_
setattr(x, 'docker_creds', docker_creds_)


from containerregistry.client.v1 import docker_http_
setattr(x, 'docker_http', docker_http_)


from containerregistry.client.v1 import docker_image_
setattr(x, 'docker_image', docker_image_)


from containerregistry.client.v1 import docker_session_
setattr(x, 'docker_session', docker_session_)


from containerregistry.client.v1 import save_
setattr(x, 'save', save_)


