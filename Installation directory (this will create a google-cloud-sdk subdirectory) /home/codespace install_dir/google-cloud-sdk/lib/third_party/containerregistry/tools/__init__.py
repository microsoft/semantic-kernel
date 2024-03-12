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
x=sys.modules['containerregistry.tools']
  

from containerregistry.tools import patched_
setattr(x, 'patched', patched_)


from containerregistry.tools import platform_args_
setattr(x, 'platform_args', platform_args_)


from containerregistry.tools import logging_setup_
setattr(x, 'logging_setup', logging_setup_)


from containerregistry.tools import docker_appender_
setattr(x, 'docker_appender', docker_appender_)


from containerregistry.tools import docker_puller_
setattr(x, 'docker_puller', docker_puller_)


from containerregistry.tools import docker_pusher_
setattr(x, 'docker_pusher', docker_pusher_)


from containerregistry.tools import fast_puller_
setattr(x, 'fast_puller', fast_puller_)


from containerregistry.tools import fast_flatten_
setattr(x, 'fast_flatten', fast_flatten_)


from containerregistry.tools import fast_importer_
setattr(x, 'fast_importer', fast_importer_)


from containerregistry.tools import fast_pusher_
setattr(x, 'fast_pusher', fast_pusher_)


from containerregistry.tools import image_digester_
setattr(x, 'image_digester', image_digester_)


