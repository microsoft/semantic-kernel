# stateMachine.py
#
# module to define .pystate import handler
#
# import imputil
import keyword
import sys
import os
import types
import importlib
try:
    import urllib.parse
    url_parse = urllib.parse.urlparse
except ImportError:
    print("import error, Python 2 not supported")
    raise
    import urllib
    url_parse = urllib.parse


DEBUG = False


import pyparsing as pp

# define basic exception for invalid state transitions - state machine classes will subclass to
# define their own specific exception type
class InvalidTransitionException(Exception): pass


ident = pp.Word(pp.alphas + "_", pp.alphanums + "_$")

# add parse-time condition to make sure we do not allow any Python keywords to be used as
# statemachine identifiers
def no_keywords_allowed(s, l, t):
    wd = t[0]
    return not keyword.iskeyword(wd)
ident.addCondition(no_keywords_allowed, message="cannot use a Python keyword for state or transition identifier")

stateTransition = ident("from_state") + "->" + ident("to_state")
stateMachine = (pp.Keyword("statemachine") + ident("name") + ":"
                + pp.OneOrMore(pp.Group(stateTransition))("transitions"))

namedStateTransition = (ident("from_state")
                        + "-(" + ident("transition") + ")->"
                        + ident("to_state"))
namedStateMachine = (pp.Keyword("statemachine") + ident("name") + ":"
                     + pp.OneOrMore(pp.Group(namedStateTransition))("transitions"))


def expand_state_definition(source, loc, tokens):
    """
    Parse action to convert statemachine to corresponding Python classes and methods
    """
    indent = " " * (pp.col(loc, source) - 1)
    statedef = []

    # build list of states
    states = set()
    fromTo = {}
    for tn in tokens.transitions:
        states.add(tn.from_state)
        states.add(tn.to_state)
        fromTo[tn.from_state] = tn.to_state

    # define base class for state classes
    baseStateClass = tokens.name
    statedef.extend([
        "class %s(object):" % baseStateClass,
        "    def __str__(self):",
        "        return self.__class__.__name__",

        "    @classmethod",
        "    def states(cls):",
        "        return list(cls.__subclasses__())",

        "    def next_state(self):",
        "        return self._next_state_class()",
    ])

    # define all state classes
    statedef.extend("class {0}({1}): pass".format(s, baseStateClass) for s in states)

    # define state->state transitions
    statedef.extend("{0}._next_state_class = {1}".format(s, fromTo[s]) for s in states if s in fromTo)

    statedef.extend([
        "class {baseStateClass}Mixin:".format(baseStateClass=baseStateClass),
        "    def __init__(self):",
        "        self._state = None",

        "    def initialize_state(self, init_state):",
        "        if issubclass(init_state, {baseStateClass}):".format(baseStateClass=baseStateClass),
        "            init_state = init_state()",
        "        self._state = init_state",

        "    @property",
        "    def state(self):",
        "        return self._state",

        "    # get behavior/properties from current state",
        "    def __getattr__(self, attrname):",
        "        attr = getattr(self._state, attrname)",
        "        return attr",

        "    def __str__(self):",
        "       return '{0}: {1}'.format(self.__class__.__name__, self._state)",
        ])

    return ("\n" + indent).join(statedef) + "\n"

stateMachine.setParseAction(expand_state_definition)


def expand_named_state_definition(source, loc, tokens):
    """
    Parse action to convert statemachine with named transitions to corresponding Python
    classes and methods
    """
    indent = " " * (pp.col(loc, source) - 1)
    statedef = []
    # build list of states and transitions
    states = set()
    transitions = set()

    baseStateClass = tokens.name

    fromTo = {}
    for tn in tokens.transitions:
        states.add(tn.from_state)
        states.add(tn.to_state)
        transitions.add(tn.transition)
        if tn.from_state in fromTo:
            fromTo[tn.from_state][tn.transition] = tn.to_state
        else:
            fromTo[tn.from_state] = {tn.transition: tn.to_state}

    # add entries for terminal states
    for s in states:
        if s not in fromTo:
            fromTo[s] = {}

    # define state transition class
    statedef.extend([
        "class {baseStateClass}Transition:".format(baseStateClass=baseStateClass),
        "    def __str__(self):",
        "        return self.transitionName",
    ])
    statedef.extend(
        "{tn_name} = {baseStateClass}Transition()".format(tn_name=tn,
                                                          baseStateClass=baseStateClass)
        for tn in transitions)
    statedef.extend("{tn_name}.transitionName = '{tn_name}'".format(tn_name=tn)
                    for tn in transitions)

    # define base class for state classes
    statedef.extend([
        "class %s(object):" % baseStateClass,
        "    from statemachine import InvalidTransitionException as BaseTransitionException",
        "    class InvalidTransitionException(BaseTransitionException): pass",
        "    def __str__(self):",
        "        return self.__class__.__name__",

        "    @classmethod",
        "    def states(cls):",
        "        return list(cls.__subclasses__())",

        "    @classmethod",
        "    def next_state(cls, name):",
        "        try:",
        "            return cls.tnmap[name]()",
        "        except KeyError:",
        "            raise cls.InvalidTransitionException('%s does not support transition %r'% (cls.__name__, name))",

        "    def __bad_tn(name):",
        "        def _fn(cls):",
        "            raise cls.InvalidTransitionException('%s does not support transition %r'% (cls.__name__, name))",
        "        _fn.__name__ = name",
        "        return _fn",
    ])

    # define default 'invalid transition' methods in base class, valid transitions will be implemented in subclasses
    statedef.extend(
        "    {tn_name} = classmethod(__bad_tn({tn_name!r}))".format(tn_name=tn)
        for tn in transitions)

    # define all state classes
    statedef.extend("class %s(%s): pass" % (s, baseStateClass)
                    for s in states)

    # define state transition methods for valid transitions from each state
    for s in states:
        trns = list(fromTo[s].items())
        # statedef.append("%s.tnmap = {%s}" % (s, ", ".join("%s:%s" % tn for tn in trns)))
        statedef.extend("%s.%s = classmethod(lambda cls: %s())" % (s, tn_, to_)
                        for tn_, to_ in trns)

    statedef.extend([
        "{baseStateClass}.transitions = classmethod(lambda cls: [{transition_class_list}])".format(
            baseStateClass=baseStateClass,
            transition_class_list = ', '.join("cls.{0}".format(tn) for tn in transitions)
        ),
        "{baseStateClass}.transition_names = [tn.__name__ for tn in {baseStateClass}.transitions()]".format(
            baseStateClass=baseStateClass
        )
    ])

    # define <state>Mixin class for application classes that delegate to the state
    statedef.extend([
        "class {baseStateClass}Mixin:".format(baseStateClass=baseStateClass),
        "    def __init__(self):",
        "        self._state = None",

        "    def initialize_state(self, init_state):",
        "        if issubclass(init_state, {baseStateClass}):".format(baseStateClass=baseStateClass),
        "            init_state = init_state()",
        "        self._state = init_state",

        "    @property",
        "    def state(self):",
        "        return self._state",

        "    # get behavior/properties from current state",
        "    def __getattr__(self, attrname):",
        "        attr = getattr(self._state, attrname)",
        "        return attr",

        "    def __str__(self):",
        "       return '{0}: {1}'.format(self.__class__.__name__, self._state)",

    ])

    # define transition methods to be delegated to the _state instance variable
    statedef.extend(
        "    def {tn_name}(self): self._state = self._state.{tn_name}()".format(tn_name=tn)
        for tn in transitions
    )
    return ("\n" + indent).join(statedef) + "\n"

namedStateMachine.setParseAction(expand_named_state_definition)


# ======================================================================
# NEW STUFF - Matt Anderson, 2009-11-26
# ======================================================================
class SuffixImporter(object):
    """An importer designed using the mechanism defined in :pep:`302`. I read
    the PEP, and also used Doug Hellmann's PyMOTW article `Modules and
    Imports`_, as a pattern.

    .. _`Modules and Imports`: http://www.doughellmann.com/PyMOTW/sys/imports.html

    Define a subclass that specifies a :attr:`suffix` attribute, and
    implements a :meth:`process_filedata` method. Then call the classmethod
    :meth:`register` on your class to actually install it in the appropriate
    places in :mod:`sys`. """

    scheme = 'suffix'
    suffix = None
    path_entry = None

    @classmethod
    def trigger_url(cls):
        if cls.suffix is None:
            raise ValueError('%s.suffix is not set' % cls.__name__)
        return 'suffix:%s' % cls.suffix

    @classmethod
    def register(cls):
        sys.path_hooks.append(cls)
        sys.path.append(cls.trigger_url())

    def __init__(self, path_entry):
        pr = url_parse(str(path_entry))
        if pr.scheme != self.scheme or pr.path != self.suffix:
            raise ImportError()
        self.path_entry = path_entry
        self._found = {}

    def checkpath_iter(self, fullname):
        for dirpath in sys.path:
            # if the value in sys.path_importer_cache is None, then this
            # path *should* be imported by the builtin mechanism, and the
            # entry is thus a path to a directory on the filesystem;
            # if it's not None, then some other importer is in charge, and
            # it probably isn't even a filesystem path
            finder = sys.path_importer_cache.get(dirpath)
            if isinstance(finder, (type(None), importlib.machinery.FileFinder)):
                checkpath = os.path.join(dirpath, '{0}.{1}'.format(fullname, self.suffix))
                yield checkpath

    def find_module(self, fullname, path=None):
        for checkpath in self.checkpath_iter(fullname):
            if os.path.isfile(checkpath):
                self._found[fullname] = checkpath
                return self
        return None

    def load_module(self, fullname):
        assert fullname in self._found
        if fullname in sys.modules:
            module = sys.modules[fullname]
        else:
            sys.modules[fullname] = module = types.ModuleType(fullname)
        data = None
        with open(self._found[fullname]) as f:
            data = f.read()

        module.__dict__.clear()
        module.__file__ = self._found[fullname]
        module.__name__ = fullname
        module.__loader__ = self
        self.process_filedata(module, data)
        return module

    def process_filedata(self, module, data):
        pass


class PystateImporter(SuffixImporter):
    suffix = 'pystate'

    def process_filedata(self, module, data):
        # MATT-NOTE: re-worked :func:`get_state_machine`

        # convert any statemachine expressions
        stateMachineExpr = (stateMachine | namedStateMachine).ignore(pp.pythonStyleComment)
        generated_code = stateMachineExpr.transformString(data)

        if DEBUG: print(generated_code)

        # compile code object from generated code
        # (strip trailing spaces and tabs, compile doesn't like
        # dangling whitespace)
        COMPILE_MODE = 'exec'

        codeobj = compile(generated_code.rstrip(" \t"),
                          module.__file__,
                          COMPILE_MODE)

        exec(codeobj, module.__dict__)


PystateImporter.register()

if DEBUG:
    print("registered {0!r} importer".format(PystateImporter.suffix))
