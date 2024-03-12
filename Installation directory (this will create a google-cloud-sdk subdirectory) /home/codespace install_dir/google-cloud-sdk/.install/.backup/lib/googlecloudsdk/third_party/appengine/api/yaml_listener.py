#
# Copyright 2007 Google LLC. All Rights Reserved.
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

"""PyYAML event listener

Contains class which interprets YAML events and forwards them to
a handler object.
"""

from __future__ import absolute_import

import copy
from ruamel import yaml

from googlecloudsdk.third_party.appengine.api import yaml_errors


# Default mapping of event type to handler method name
_EVENT_METHOD_MAP = {
  yaml.events.StreamStartEvent: 'StreamStart',
  yaml.events.StreamEndEvent: 'StreamEnd',
  yaml.events.DocumentStartEvent: 'DocumentStart',
  yaml.events.DocumentEndEvent: 'DocumentEnd',
  yaml.events.AliasEvent: 'Alias',
  yaml.events.ScalarEvent: 'Scalar',
  yaml.events.SequenceStartEvent: 'SequenceStart',
  yaml.events.SequenceEndEvent: 'SequenceEnd',
  yaml.events.MappingStartEvent: 'MappingStart',
  yaml.events.MappingEndEvent: 'MappingEnd',
}


class EventHandler(object):
  """Handler interface for parsing YAML files.

  Implement this interface to define specific YAML event handling class.
  Implementing classes instances are passed to the constructor of
  EventListener to act as a receiver of YAML parse events.
  """
  def StreamStart(self, event, loader):
    """Handle start of stream event"""

  def StreamEnd(self, event, loader):
    """Handle end of stream event"""

  def DocumentStart(self, event, loader):
    """Handle start of document event"""

  def DocumentEnd(self, event, loader):
    """Handle end of document event"""

  def Alias(self, event, loader):
    """Handle alias event"""

  def Scalar(self, event, loader):
    """Handle scalar event"""

  def SequenceStart(self, event, loader):
    """Handle start of sequence event"""

  def SequenceEnd(self, event, loader):
    """Handle end of sequence event"""

  def MappingStart(self, event, loader):
    """Handle start of mapping event"""

  def MappingEnd(self, event, loader):
    """Handle end of mapping event"""


class EventListener(object):
  """Helper class to re-map PyYAML events to method calls.

  By default, PyYAML generates its events via a Python generator.  This class
  is a helper that iterates over the events from the PyYAML parser and forwards
  them to a handle class in the form of method calls.  For simplicity, the
  underlying event is forwarded to the handler as a parameter to the call.

  This object does not itself produce iterable objects, but is really a mapping
  to a given handler instance.

    Example use:

      class PrintDocumentHandler(object):
        def DocumentStart(event):
          print "A new document has been started"

      EventListener(PrintDocumentHandler()).Parse('''
        key1: value1
        ---
        key2: value2
        '''

      >>> A new document has been started
          A new document has been started

  In the example above, the implemented handler class (PrintDocumentHandler)
  has a single method which reports each time a new document is started within
  a YAML file.  It is not necessary to subclass the EventListener, merely it
  receives a PrintDocumentHandler instance.  Every time a new document begins,
  PrintDocumentHandler.DocumentStart is called with the PyYAML event passed
  in as its parameter..
  """

  def __init__(self, event_handler):
    """Initialize PyYAML event listener.

    Constructs internal mapping directly from event type to method on actual
    handler.  This prevents reflection being used during actual parse time.

    Args:
      event_handler: Event handler that will receive mapped events. Must
        implement at least one appropriate handler method named from
        the values of the _EVENT_METHOD_MAP.

    Raises:
      ListenerConfigurationError if event_handler is not an EventHandler.
    """
    if not isinstance(event_handler, EventHandler):
      raise yaml_errors.ListenerConfigurationError(
        'Must provide event handler of type yaml_listener.EventHandler')
    self._event_method_map = {}
    # For each event type in default method map...
    for event, method in _EVENT_METHOD_MAP.items():
      # Map event class to actual method
      self._event_method_map[event] = getattr(event_handler, method)

  def HandleEvent(self, event, loader=None):
    """Handle individual PyYAML event.

    Args:
      event: Event to forward to method call in method call.

    Raises:
      IllegalEvent when receives an unrecognized or unsupported event type.
    """
    # Must be valid event object
    if event.__class__ not in _EVENT_METHOD_MAP:
      raise yaml_errors.IllegalEvent(
            "%s is not a valid PyYAML class" % event.__class__.__name__)
    # Conditionally handle event
    if event.__class__ in self._event_method_map:
      self._event_method_map[event.__class__](event, loader)

  def _HandleEvents(self, events):
    """Iterate over all events and send them to handler.

    This method is not meant to be called from the interface.

    Only use in tests.

    Args:
      events: Iterator or generator containing events to process.
    raises:
      EventListenerParserError when a yaml.parser.ParserError is raised.
      EventError when an exception occurs during the handling of an event.
    """
    for event in events:
      try:
        self.HandleEvent(*event)
      except Exception as e:
        event_object, loader = event
        raise yaml_errors.EventError(e, event_object)

  def _GenerateEventParameters(self,
                               stream,
                               loader_class=yaml.loader.SafeLoader,
                               **loader_args
                              ):
    """Creates a generator that yields event, loader parameter pairs.

    For use as parameters to HandleEvent method for use by Parse method.
    During testing, _GenerateEventParameters is simulated by allowing
    the harness to pass in a list of pairs as the parameter.

    A list of (event, loader) pairs must be passed to _HandleEvents otherwise
    it is not possible to pass the loader instance to the handler.

    Also responsible for instantiating the loader from the Loader
    parameter.

    Args:
      stream: String document or open file object to process as per the
        yaml.parse method.  Any object that implements a 'read()' method which
        returns a string document will work.
      loader_class: Loader class to use as per the yaml.parse method.  Used to
        instantiate new yaml.loader instance.
      **loader_args: Pass to the loader on construction


    Yields:
      Tuple(event, loader) where:
        event: Event emitted by PyYAML loader.
        loader: Used for dependency injection.
    """
    assert loader_class is not None
    try:
      loader = loader_class(stream, **loader_args)
      while loader.check_event():
        yield (loader.get_event(), loader)
    except yaml.error.YAMLError as e:
      raise yaml_errors.EventListenerYAMLError(e)

  def Parse(self, stream, loader_class=yaml.loader.SafeLoader, **loader_args):
    """Call YAML parser to generate and handle all events.

    Calls PyYAML parser and sends resulting generator to handle_event method
    for processing.

    Args:
      stream: String document or open file object to process as per the
        yaml.parse method.  Any object that implements a 'read()' method which
        returns a string document will work with the YAML parser.
      loader_class: Used for dependency injection.
      **loader_args: Pass to the loader on construction.
    """
    # Set the default version to be YAML 1.1 for backwards compatibility, but
    # allow overides.
    version = (1, 1)
    if 'version' in loader_args:
      loader_args = copy.copy(loader_args)
      version = loader_args['version']
      del loader_args['version']
    self._HandleEvents(self._GenerateEventParameters(
        stream, loader_class, version=version, **loader_args))
