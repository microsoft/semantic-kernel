#!/usr/bin/env python
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
import getopt
import sys
import importlib
import time
import boto

usage_string = """
SYNOPSIS
    launch_ami.py -a ami_id [-b script_bucket] [-s script_name]
                  [-m module] [-c class_name] [-r]
                  [-g group] [-k key_name] [-n num_instances]
                  [-w] [extra_data]
    Where:
        ami_id - the id of the AMI you wish to launch
        module - The name of the Python module containing the class you
                 want to run when the instance is started.  If you use this
                 option the Python module must already be stored on the
                 instance in a location that is on the Python path.
        script_file - The name of a local Python module that you would like
                      to have copied to S3 and then run on the instance
                      when it is started.  The specified module must be
                      import'able (i.e. in your local Python path).  It
                      will then be copied to the specified bucket in S3
                      (see the -b option).  Once the new instance(s)
                      start up the script will be copied from S3 and then
                      run locally on the instance.
        class_name - The name of the class to be instantiated within the
                     module or script file specified.
        script_bucket - the name of the bucket in which the script will be
                        stored
        group - the name of the security group the instance will run in
        key_name - the name of the keypair to use when launching the AMI
        num_instances - how many instances of the AMI to launch (default 1)
        input_queue_name - Name of SQS to read input messages from
        output_queue_name - Name of SQS to write output messages to
        extra_data - additional name-value pairs that will be passed as
                     userdata to the newly launched instance.  These should
                     be of the form "name=value"
        The -r option reloads the Python module to S3 without launching
        another instance.  This can be useful during debugging to allow
        you to test a new version of your script without shutting down
        your instance and starting up another one.
        The -w option tells the script to run synchronously, meaning to
        wait until the instance is actually up and running.  It then prints
        the IP address and internal and external DNS names before exiting.
"""

def usage():
    print(usage_string)
    sys.exit()

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:b:c:g:hi:k:m:n:o:rs:w',
                                   ['ami', 'bucket', 'class', 'group', 'help',
                                    'inputqueue', 'keypair', 'module',
                                    'numinstances', 'outputqueue',
                                    'reload', 'script_name', 'wait'])
    except:
        usage()
    params = {'module_name': None,
              'script_name': None,
              'class_name': None,
              'script_bucket': None,
              'group': 'default',
              'keypair': None,
              'ami': None,
              'num_instances': 1,
              'input_queue_name': None,
              'output_queue_name': None}
    reload = None
    wait = None
    for o, a in opts:
        if o in ('-a', '--ami'):
            params['ami'] = a
        if o in ('-b', '--bucket'):
            params['script_bucket'] = a
        if o in ('-c', '--class'):
            params['class_name'] = a
        if o in ('-g', '--group'):
            params['group'] = a
        if o in ('-h', '--help'):
            usage()
        if o in ('-i', '--inputqueue'):
            params['input_queue_name'] = a
        if o in ('-k', '--keypair'):
            params['keypair'] = a
        if o in ('-m', '--module'):
            params['module_name'] = a
        if o in ('-n', '--num_instances'):
            params['num_instances'] = int(a)
        if o in ('-o', '--outputqueue'):
            params['output_queue_name'] = a
        if o in ('-r', '--reload'):
            reload = True
        if o in ('-s', '--script'):
            params['script_name'] = a
        if o in ('-w', '--wait'):
            wait = True

    # check required fields
    required = ['ami']
    for pname in required:
        if not params.get(pname, None):
            print('%s is required' % pname)
            usage()
    if params['script_name']:
        # first copy the desired module file to S3 bucket
        if reload:
            print('Reloading module %s to S3' % params['script_name'])
        else:
            print('Copying module %s to S3' % params['script_name'])
        l = importlib.util.find_spec(params['script_name'])
        c = boto.connect_s3()
        bucket = c.get_bucket(params['script_bucket'])
        key = bucket.new_key(params['script_name'] + '.py')
        key.set_contents_from_file(l[0])
        params['script_md5'] = key.md5
    # we have everything we need, now build userdata string
    l = []
    for k, v in params.items():
        if v:
            l.append('%s=%s' % (k, v))
    c = boto.connect_ec2()
    l.append('aws_access_key_id=%s' % c.aws_access_key_id)
    l.append('aws_secret_access_key=%s' % c.aws_secret_access_key)
    for kv in args:
        l.append(kv)
    s = '|'.join(l)
    if not reload:
        rs = c.get_all_images([params['ami']])
        img = rs[0]
        r = img.run(user_data=s, key_name=params['keypair'],
                    security_groups=[params['group']],
                    max_count=params.get('num_instances', 1))
        print('AMI: %s - %s (Started)' % (params['ami'], img.location))
        print('Reservation %s contains the following instances:' % r.id)
        for i in r.instances:
            print('\t%s' % i.id)
        if wait:
            running = False
            while not running:
                time.sleep(30)
                [i.update() for i in r.instances]
                status = [i.state for i in r.instances]
                print(status)
                if status.count('running') == len(r.instances):
                    running = True
            for i in r.instances:
                print('Instance: %s' % i.ami_launch_index)
                print('Public DNS Name: %s' % i.public_dns_name)
                print('Private DNS Name: %s' % i.private_dns_name)

if __name__ == "__main__":
    main()
