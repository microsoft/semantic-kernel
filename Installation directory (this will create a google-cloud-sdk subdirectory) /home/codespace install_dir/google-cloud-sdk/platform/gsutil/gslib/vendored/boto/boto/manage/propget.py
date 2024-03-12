# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

def get(prop, choices=None):
    prompt = prop.verbose_name
    if not prompt:
        prompt = prop.name
    if choices:
        if callable(choices):
            choices = choices()
    else:
        choices = prop.get_choices()
    valid = False
    while not valid:
        if choices:
            min = 1
            max = len(choices)
            for i in range(min, max+1):
                value = choices[i-1]
                if isinstance(value, tuple):
                    value = value[0]
                print('[%d] %s' % (i, value))
            value = raw_input('%s [%d-%d]: ' % (prompt, min, max))
            try:
                int_value = int(value)
                value = choices[int_value-1]
                if isinstance(value, tuple):
                    value = value[1]
                valid = True
            except ValueError:
                print('%s is not a valid choice' % value)
            except IndexError:
                print('%s is not within the range[%d-%d]' % (min, max))
        else:
            value = raw_input('%s: ' % prompt)
            try:
                value = prop.validate(value)
                if prop.empty(value) and prop.required:
                    print('A value is required')
                else:
                    valid = True
            except:
                print('Invalid value: %s' % value)
    return value
        
