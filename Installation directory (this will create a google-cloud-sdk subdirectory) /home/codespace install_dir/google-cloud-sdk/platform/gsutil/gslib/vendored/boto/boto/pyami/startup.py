# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
import sys
import boto
from boto.utils import find_class
from boto import config
from boto.pyami.scriptbase import ScriptBase


class Startup(ScriptBase):

    def run_scripts(self):
        scripts = config.get('Pyami', 'scripts')
        if scripts:
            for script in scripts.split(','):
                script = script.strip(" ")
                try:
                    pos = script.rfind('.')
                    if pos > 0:
                        mod_name = script[0:pos]
                        cls_name = script[pos + 1:]
                        cls = find_class(mod_name, cls_name)
                        boto.log.info('Running Script: %s' % script)
                        s = cls()
                        s.main()
                    else:
                        boto.log.warning('Trouble parsing script: %s' % script)
                except Exception as e:
                    boto.log.exception('Problem Running Script: %s. Startup process halting.' % script)
                    raise e

    def main(self):
        self.run_scripts()
        self.notify('Startup Completed for %s' % config.get('Instance', 'instance-id'))

if __name__ == "__main__":
    if not config.has_section('loggers'):
        boto.set_file_logger('startup', '/var/log/boto.log')
    sys.path.append(config.get('Pyami', 'working_dir'))
    su = Startup()
    su.main()
