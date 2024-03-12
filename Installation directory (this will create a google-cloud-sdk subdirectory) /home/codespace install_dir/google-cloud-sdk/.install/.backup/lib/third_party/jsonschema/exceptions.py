from collections import defaultdict, deque
import itertools
import pprint
import textwrap

from jsonschema import _utils
from jsonschema.compat import PY3, iteritems


WEAK_MATCHES = frozenset(["anyOf", "oneOf"])
STRONG_MATCHES = frozenset()

_unset = _utils.Unset()


class _Error(Exception):
    def __init__(
        self,
        message,
        validator=_unset,
        path=(),
        cause=None,
        context=(),
        validator_value=_unset,
        instance=_unset,
        schema=_unset,
        schema_path=(),
        parent=None,
    ):
        super(_Error, self).__init__(
            message,
            validator,
            path,
            cause,
            context,
            validator_value,
            instance,
            schema,
            schema_path,
            parent,
        )
        self.message = message
        self.path = self.relative_path = deque(path)
        self.schema_path = self.relative_schema_path = deque(schema_path)
        self.context = list(context)
        self.cause = self.__cause__ = cause
        self.validator = validator
        self.validator_value = validator_value
        self.instance = instance
        self.schema = schema
        self.parent = parent

        for error in context:
            error.parent = self

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self.message)

    def __unicode__(self):
        essential_for_verbose = (
            self.validator, self.validator_value, self.instance, self.schema,
        )
        if any(m is _unset for m in essential_for_verbose):
            return self.message

        pschema = pprint.pformat(self.schema, width=72)
        pinstance = pprint.pformat(self.instance, width=72)
        return self.message + textwrap.dedent("""

            Failed validating %r in schema%s:
            %s

            On instance%s:
            %s
            """.rstrip()
        ) % (
            self.validator,
            _utils.format_as_index(list(self.relative_schema_path)[:-1]),
            _utils.indent(pschema),
            _utils.format_as_index(self.relative_path),
            _utils.indent(pinstance),
        )

    if PY3:
        __str__ = __unicode__
    else:
        def __str__(self):
            return unicode(self).encode("utf-8")

    @classmethod
    def create_from(cls, other):
        return cls(**other._contents())

    @property
    def absolute_path(self):
        parent = self.parent
        if parent is None:
            return self.relative_path

        path = deque(self.relative_path)
        path.extendleft(reversed(parent.absolute_path))
        return path

    @property
    def absolute_schema_path(self):
        parent = self.parent
        if parent is None:
            return self.relative_schema_path

        path = deque(self.relative_schema_path)
        path.extendleft(reversed(parent.absolute_schema_path))
        return path

    def _set(self, **kwargs):
        for k, v in iteritems(kwargs):
            if getattr(self, k) is _unset:
                setattr(self, k, v)

    def _contents(self):
        attrs = (
            "message", "cause", "context", "validator", "validator_value",
            "path", "schema_path", "instance", "schema", "parent",
        )
        return dict((attr, getattr(self, attr)) for attr in attrs)


class ValidationError(_Error):
    pass


class SchemaError(_Error):
    pass


class RefResolutionError(Exception):
    pass


class UnknownType(Exception):
    def __init__(self, type, instance, schema):
        self.type = type
        self.instance = instance
        self.schema = schema

    def __unicode__(self):
        pschema = pprint.pformat(self.schema, width=72)
        pinstance = pprint.pformat(self.instance, width=72)
        return textwrap.dedent("""
            Unknown type %r for validator with schema:
            %s

            While checking instance:
            %s
            """.rstrip()
        ) % (self.type, _utils.indent(pschema), _utils.indent(pinstance))

    if PY3:
        __str__ = __unicode__
    else:
        def __str__(self):
            return unicode(self).encode("utf-8")


class FormatError(Exception):
    def __init__(self, message, cause=None):
        super(FormatError, self).__init__(message, cause)
        self.message = message
        self.cause = self.__cause__ = cause

    def __unicode__(self):
        return self.message

    if PY3:
        __str__ = __unicode__
    else:
        def __str__(self):
            return self.message.encode("utf-8")


class ErrorTree(object):
    """
    ErrorTrees make it easier to check which validations failed.

    """

    _instance = _unset

    def __init__(self, errors=()):
        self.errors = {}
        self._contents = defaultdict(self.__class__)

        for error in errors:
            container = self
            for element in error.path:
                container = container[element]
            container.errors[error.validator] = error

            container._instance = error.instance

    def __contains__(self, index):
        """
        Check whether ``instance[index]`` has any errors.

        """

        return index in self._contents

    def __getitem__(self, index):
        """
        Retrieve the child tree one level down at the given ``index``.

        If the index is not in the instance that this tree corresponds to and
        is not known by this tree, whatever error would be raised by
        ``instance.__getitem__`` will be propagated (usually this is some
        subclass of :class:`LookupError`.

        """

        if self._instance is not _unset and index not in self:
            self._instance[index]
        return self._contents[index]

    def __setitem__(self, index, value):
        self._contents[index] = value

    def __iter__(self):
        """
        Iterate (non-recursively) over the indices in the instance with errors.

        """

        return iter(self._contents)

    def __len__(self):
        """
        Same as :attr:`total_errors`.

        """

        return self.total_errors

    def __repr__(self):
        return "<%s (%s total errors)>" % (self.__class__.__name__, len(self))

    @property
    def total_errors(self):
        """
        The total number of errors in the entire tree, including children.

        """

        child_errors = sum(len(tree) for _, tree in iteritems(self._contents))
        return len(self.errors) + child_errors


def by_relevance(weak=WEAK_MATCHES, strong=STRONG_MATCHES):
    def relevance(error):
        validator = error.validator
        return -len(error.path), validator not in weak, validator in strong
    return relevance


relevance = by_relevance()


def best_match(errors, key=relevance):
    errors = iter(errors)
    best = next(errors, None)
    if best is None:
        return
    best = max(itertools.chain([best], errors), key=key)

    while best.context:
        best = min(best.context, key=key)
    return best
