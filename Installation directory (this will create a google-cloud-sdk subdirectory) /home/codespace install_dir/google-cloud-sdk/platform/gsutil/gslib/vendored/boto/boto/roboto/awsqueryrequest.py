# Copyright (c) 2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
import sys
import os
import boto
import optparse
import copy
import boto.exception
import boto.roboto.awsqueryservice

import bdb
import traceback
try:
    import epdb as debugger
except ImportError:
    import pdb as debugger

def boto_except_hook(debugger_flag, debug_flag):
    def excepthook(typ, value, tb):
        if typ is bdb.BdbQuit:
            sys.exit(1)
        sys.excepthook = sys.__excepthook__

        if debugger_flag and sys.stdout.isatty() and sys.stdin.isatty():
            if debugger.__name__ == 'epdb':
                debugger.post_mortem(tb, typ, value)
            else:
                debugger.post_mortem(tb)
        elif debug_flag:
            print(traceback.print_tb(tb))
            sys.exit(1)
        else:
            print(value)
            sys.exit(1)

    return excepthook

class Line(object):

    def __init__(self, fmt, data, label):
        self.fmt = fmt
        self.data = data
        self.label = label
        self.line = '%s\t' % label
        self.printed = False

    def append(self, datum):
        self.line += '%s\t' % datum

    def print_it(self):
        if not self.printed:
            print(self.line)
            self.printed = True

class RequiredParamError(boto.exception.BotoClientError):

    def __init__(self, required):
        self.required = required
        s = 'Required parameters are missing: %s' % self.required
        super(RequiredParamError, self).__init__(s)

class EncoderError(boto.exception.BotoClientError):

    def __init__(self, error_msg):
        s = 'Error encoding value (%s)' % error_msg
        super(EncoderError, self).__init__(s)

class FilterError(boto.exception.BotoClientError):

    def __init__(self, filters):
        self.filters = filters
        s = 'Unknown filters: %s' % self.filters
        super(FilterError, self).__init__(s)

class Encoder(object):

    @classmethod
    def encode(cls, p, rp, v, label=None):
        if p.name.startswith('_'):
            return
        try:
            mthd = getattr(cls, 'encode_'+p.ptype)
            mthd(p, rp, v, label)
        except AttributeError:
            raise EncoderError('Unknown type: %s' % p.ptype)

    @classmethod
    def encode_string(cls, p, rp, v, l):
        if l:
            label = l
        else:
            label = p.name
        rp[label] = v

    encode_file = encode_string
    encode_enum = encode_string

    @classmethod
    def encode_integer(cls, p, rp, v, l):
        if l:
            label = l
        else:
            label = p.name
        rp[label] = '%d' % v

    @classmethod
    def encode_boolean(cls, p, rp, v, l):
        if l:
            label = l
        else:
            label = p.name
        if v:
            v = 'true'
        else:
            v = 'false'
        rp[label] = v

    @classmethod
    def encode_datetime(cls, p, rp, v, l):
        if l:
            label = l
        else:
            label = p.name
        rp[label] = v

    @classmethod
    def encode_array(cls, p, rp, v, l):
        v = boto.utils.mklist(v)
        if l:
            label = l
        else:
            label = p.name
        label = label + '.%d'
        for i, value in enumerate(v):
            rp[label%(i+1)] = value

class AWSQueryRequest(object):

    ServiceClass = None

    Description = ''
    Params = []
    Args = []
    Filters = []
    Response = {}

    CLITypeMap = {'string' : 'string',
                  'integer' : 'int',
                  'int' : 'int',
                  'enum' : 'choice',
                  'datetime' : 'string',
                  'dateTime' : 'string',
                  'file' : 'string',
                  'boolean' : None}

    @classmethod
    def name(cls):
        return cls.__name__

    def __init__(self, **args):
        self.args = args
        self.parser = None
        self.cli_options = None
        self.cli_args = None
        self.cli_output_format = None
        self.connection = None
        self.list_markers = []
        self.item_markers = []
        self.request_params = {}
        self.connection_args = None

    def __repr__(self):
        return self.name()

    def get_connection(self, **args):
        if self.connection is None:
            self.connection = self.ServiceClass(**args)
        return self.connection

    @property
    def status(self):
        retval = None
        if self.http_response is not None:
            retval = self.http_response.status
        return retval

    @property
    def reason(self):
        retval = None
        if self.http_response is not None:
            retval = self.http_response.reason
        return retval

    @property
    def request_id(self):
        retval = None
        if self.aws_response is not None:
            retval = getattr(self.aws_response, 'requestId')
        return retval

    def process_filters(self):
        filters = self.args.get('filters', [])
        filter_names = [f['name'] for f in self.Filters]
        unknown_filters = [f for f in filters if f not in filter_names]
        if unknown_filters:
            raise FilterError('Unknown filters: %s' % unknown_filters)
        for i, filter in enumerate(self.Filters):
            name = filter['name']
            if name in filters:
                self.request_params['Filter.%d.Name' % (i+1)] = name
                for j, value in enumerate(boto.utils.mklist(filters[name])):
                    Encoder.encode(filter, self.request_params, value,
                                   'Filter.%d.Value.%d' % (i+1, j+1))

    def process_args(self, **args):
        """
        Responsible for walking through Params defined for the request and:

        * Matching them with keyword parameters passed to the request
          constructor or via the command line.
        * Checking to see if all required parameters have been specified
          and raising an exception, if not.
        * Encoding each value into the set of request parameters that will
          be sent in the request to the AWS service.
        """
        self.args.update(args)
        self.connection_args = copy.copy(self.args)
        if 'debug' in self.args and self.args['debug'] >= 2:
            boto.set_stream_logger(self.name())
        required = [p.name for p in self.Params+self.Args if not p.optional]
        for param in self.Params+self.Args:
            if param.long_name:
                python_name = param.long_name.replace('-', '_')
            else:
                python_name = boto.utils.pythonize_name(param.name, '_')
            value = None
            if python_name in self.args:
                value = self.args[python_name]
            if value is None:
                value = param.default
            if value is not None:
                if param.name in required:
                    required.remove(param.name)
                if param.request_param:
                    if param.encoder:
                        param.encoder(param, self.request_params, value)
                    else:
                        Encoder.encode(param, self.request_params, value)
            if python_name in self.args:
                del self.connection_args[python_name]
        if required:
            l = []
            for p in self.Params+self.Args:
                if p.name in required:
                    if p.short_name and p.long_name:
                        l.append('(%s, %s)' % (p.optparse_short_name,
                                               p.optparse_long_name))
                    elif p.short_name:
                        l.append('(%s)' % p.optparse_short_name)
                    else:
                        l.append('(%s)' % p.optparse_long_name)
            raise RequiredParamError(','.join(l))
        boto.log.debug('request_params: %s' % self.request_params)
        self.process_markers(self.Response)

    def process_markers(self, fmt, prev_name=None):
        if fmt and fmt['type'] == 'object':
            for prop in fmt['properties']:
                self.process_markers(prop, fmt['name'])
        elif fmt and fmt['type'] == 'array':
            self.list_markers.append(prev_name)
            self.item_markers.append(fmt['name'])

    def send(self, verb='GET', **args):
        self.process_args(**args)
        self.process_filters()
        conn = self.get_connection(**self.connection_args)
        self.http_response = conn.make_request(self.name(),
                                               self.request_params,
                                               verb=verb)
        self.body = self.http_response.read()
        boto.log.debug(self.body)
        if self.http_response.status == 200:
            self.aws_response = boto.jsonresponse.Element(list_marker=self.list_markers,
                                                          item_marker=self.item_markers)
            h = boto.jsonresponse.XmlHandler(self.aws_response, self)
            h.parse(self.body)
            return self.aws_response
        else:
            boto.log.error('%s %s' % (self.http_response.status,
                                      self.http_response.reason))
            boto.log.error('%s' % self.body)
            raise conn.ResponseError(self.http_response.status,
                                     self.http_response.reason,
                                     self.body)

    def add_standard_options(self):
        group = optparse.OptionGroup(self.parser, 'Standard Options')
        # add standard options that all commands get
        group.add_option('-D', '--debug', action='store_true',
                         help='Turn on all debugging output')
        group.add_option('--debugger', action='store_true',
                         default=False,
                         help='Enable interactive debugger on error')
        group.add_option('-U', '--url', action='store',
                         help='Override service URL with value provided')
        group.add_option('--region', action='store',
                         help='Name of the region to connect to')
        group.add_option('-I', '--access-key-id', action='store',
                         help='Override access key value')
        group.add_option('-S', '--secret-key', action='store',
                         help='Override secret key value')
        group.add_option('--version', action='store_true',
                         help='Display version string')
        if self.Filters:
            self.group.add_option('--help-filters', action='store_true',
                                   help='Display list of available filters')
            self.group.add_option('--filter', action='append',
                                   metavar=' name=value',
                                   help='A filter for limiting the results')
        self.parser.add_option_group(group)

    def process_standard_options(self, options, args, d):
        if hasattr(options, 'help_filters') and options.help_filters:
            print('Available filters:')
            for filter in self.Filters:
                print('%s\t%s' % (filter.name, filter.doc))
            sys.exit(0)
        if options.debug:
            self.args['debug'] = 2
        if options.url:
            self.args['url'] = options.url
        if options.region:
            self.args['region'] = options.region
        if options.access_key_id:
            self.args['aws_access_key_id'] = options.access_key_id
        if options.secret_key:
            self.args['aws_secret_access_key'] = options.secret_key
        if options.version:
            # TODO - Where should the version # come from?
            print('version x.xx')
            exit(0)
        sys.excepthook = boto_except_hook(options.debugger,
                                          options.debug)

    def get_usage(self):
        s = 'usage: %prog [options] '
        l = [ a.long_name for a in self.Args ]
        s += ' '.join(l)
        for a in self.Args:
            if a.doc:
                s += '\n\n\t%s - %s' % (a.long_name, a.doc)
        return s

    def build_cli_parser(self):
        self.parser = optparse.OptionParser(description=self.Description,
                                            usage=self.get_usage())
        self.add_standard_options()
        for param in self.Params:
            ptype = action = choices = None
            if param.ptype in self.CLITypeMap:
                ptype = self.CLITypeMap[param.ptype]
                action = 'store'
            if param.ptype == 'boolean':
                action = 'store_true'
            elif param.ptype == 'array':
                if len(param.items) == 1:
                    ptype = param.items[0]['type']
                    action = 'append'
            elif param.cardinality != 1:
                action = 'append'
            if ptype or action == 'store_true':
                if param.short_name:
                    self.parser.add_option(param.optparse_short_name,
                                           param.optparse_long_name,
                                           action=action, type=ptype,
                                           choices=param.choices,
                                           help=param.doc)
                elif param.long_name:
                    self.parser.add_option(param.optparse_long_name,
                                           action=action, type=ptype,
                                           choices=param.choices,
                                           help=param.doc)

    def do_cli(self):
        if not self.parser:
            self.build_cli_parser()
        self.cli_options, self.cli_args = self.parser.parse_args()
        d = {}
        self.process_standard_options(self.cli_options, self.cli_args, d)
        for param in self.Params:
            if param.long_name:
                p_name = param.long_name.replace('-', '_')
            else:
                p_name = boto.utils.pythonize_name(param.name)
            value = getattr(self.cli_options, p_name)
            if param.ptype == 'file' and value:
                if value == '-':
                    value = sys.stdin.read()
                else:
                    path = os.path.expanduser(value)
                    path = os.path.expandvars(path)
                    if os.path.isfile(path):
                        fp = open(path)
                        value = fp.read()
                        fp.close()
                    else:
                        self.parser.error('Unable to read file: %s' % path)
            d[p_name] = value
        for arg in self.Args:
            if arg.long_name:
                p_name = arg.long_name.replace('-', '_')
            else:
                p_name = boto.utils.pythonize_name(arg.name)
            value = None
            if arg.cardinality == 1:
                if len(self.cli_args) >= 1:
                    value = self.cli_args[0]
            else:
                value = self.cli_args
            d[p_name] = value
        self.args.update(d)
        if hasattr(self.cli_options, 'filter') and self.cli_options.filter:
            d = {}
            for filter in self.cli_options.filter:
                name, value = filter.split('=')
                d[name] = value
            if 'filters' in self.args:
                self.args['filters'].update(d)
            else:
                self.args['filters'] = d
        try:
            response = self.main()
            self.cli_formatter(response)
        except RequiredParamError as e:
            print(e)
            sys.exit(1)
        except self.ServiceClass.ResponseError as err:
            print('Error(%s): %s' % (err.error_code, err.error_message))
            sys.exit(1)
        except boto.roboto.awsqueryservice.NoCredentialsError as err:
            print('Unable to find credentials.')
            sys.exit(1)
        except Exception as e:
            print(e)
            sys.exit(1)

    def _generic_cli_formatter(self, fmt, data, label=''):
        if fmt['type'] == 'object':
            for prop in fmt['properties']:
                if 'name' in fmt:
                    if fmt['name'] in data:
                        data = data[fmt['name']]
                    if fmt['name'] in self.list_markers:
                        label = fmt['name']
                        if label[-1] == 's':
                            label = label[0:-1]
                        label = label.upper()
                self._generic_cli_formatter(prop, data, label)
        elif fmt['type'] == 'array':
            for item in data:
                line = Line(fmt, item, label)
                if isinstance(item, dict):
                    for field_name in item:
                        line.append(item[field_name])
                elif isinstance(item, basestring):
                    line.append(item)
                line.print_it()

    def cli_formatter(self, data):
        """
        This method is responsible for formatting the output for the
        command line interface.  The default behavior is to call the
        generic CLI formatter which attempts to print something
        reasonable.  If you want specific formatting, you should
        override this method and do your own thing.

        :type data: dict
        :param data: The data returned by AWS.
        """
        if data:
            self._generic_cli_formatter(self.Response, data)


