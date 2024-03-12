#
# simple_unit_tests.py
#
# While these unit tests *do* perform low-level unit testing of the classes in pyparsing,
# this testing module should also serve an instructional purpose, to clearly show simple passing
# and failing parse cases of some basic pyparsing expressions.
#
# Copyright (c) 2018  Paul T. McGuire
#
from __future__ import division

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import pyparsing as pp
from collections import namedtuple
from datetime import datetime

# Test spec data class for specifying simple pyparsing test cases
PpTestSpec = namedtuple("PpTestSpec", "desc expr text parse_fn "
                                      "expected_list expected_dict expected_fail_locn")
PpTestSpec.__new__.__defaults__ = ('', pp.Empty(), '', 'parseString', None, None, None)


class PyparsingExpressionTestCase(unittest.TestCase):
    """
    Base pyparsing testing class to parse various pyparsing expressions against
    given text strings. Subclasses must define a class attribute 'tests' which
    is a list of PpTestSpec instances.
    """
    
    if not hasattr(unittest.TestCase, 'subTest'):
        # Python 2 compatibility
        from contextlib import contextmanager
        @contextmanager
        def subTest(self, **params):
            print('subTest:', params)
            yield
    
    tests = []
    def runTest(self):
        if self.__class__ is PyparsingExpressionTestCase:
            return

        for test_spec in self.tests:
            # for each spec in the class's tests list, create a subtest
            # that will either:
            #  - parse the string with expected success, display the
            #    results, and validate the returned ParseResults
            #  - or parse the string with expected failure, display the
            #    error message and mark the error location, and validate
            #    the location against an expected value
            with self.subTest(test_spec=test_spec):
                test_spec.expr.streamline()
                print("\n{0} - {1}({2})".format(test_spec.desc,
                                                type(test_spec.expr).__name__,
                                                test_spec.expr))

                parsefn = getattr(test_spec.expr, test_spec.parse_fn)
                if test_spec.expected_fail_locn is None:
                    # expect success
                    result = parsefn(test_spec.text)
                    if test_spec.parse_fn == 'parseString':
                        print(result.dump())
                        # compare results against given list and/or dict
                        if test_spec.expected_list is not None:
                            self.assertEqual(result.asList(), test_spec.expected_list)
                        if test_spec.expected_dict is not None:
                            self.assertEqual(result.asDict(), test_spec.expected_dict)
                    elif test_spec.parse_fn == 'transformString':
                        print(result)
                        # compare results against given list and/or dict
                        if test_spec.expected_list is not None:
                            self.assertEqual([result], test_spec.expected_list)
                    elif test_spec.parse_fn == 'searchString':
                        print(result)
                        # compare results against given list and/or dict
                        if test_spec.expected_list is not None:
                            self.assertEqual([result], test_spec.expected_list)
                else:
                    # expect fail
                    try:
                        parsefn(test_spec.text)
                    except Exception as exc:
                        if not hasattr(exc, '__traceback__'):
                            # Python 2 compatibility
                            from sys import exc_info
                            etype, value, traceback = exc_info()
                            exc.__traceback__ = traceback
                        print(pp.ParseException.explain(exc))
                        self.assertEqual(exc.loc, test_spec.expected_fail_locn)
                    else:
                        self.assertTrue(False, "failed to raise expected exception")


# =========== TEST DEFINITIONS START HERE ==============

class TestLiteral(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "Simple match",
            expr = pp.Literal("xyz"),
            text = "xyz",
            expected_list = ["xyz"],
        ),
        PpTestSpec(
            desc = "Simple match after skipping whitespace",
            expr = pp.Literal("xyz"),
            text = "  xyz",
            expected_list = ["xyz"],
        ),
        PpTestSpec(
            desc = "Simple fail - parse an empty string",
            expr = pp.Literal("xyz"),
            text = "",
            expected_fail_locn = 0,
        ),
        PpTestSpec(
            desc = "Simple fail - parse a mismatching string",
            expr = pp.Literal("xyz"),
            text = "xyu",
            expected_fail_locn = 0,
        ),
        PpTestSpec(
            desc = "Simple fail - parse a partially matching string",
            expr = pp.Literal("xyz"),
            text = "xy",
            expected_fail_locn = 0,
        ),
        PpTestSpec(
            desc = "Fail - parse a partially matching string by matching individual letters",
            expr =  pp.Literal("x") + pp.Literal("y") + pp.Literal("z"),
            text = "xy",
            expected_fail_locn = 2,
        ),
    ]

class TestCaselessLiteral(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "Match colors, converting to consistent case",
            expr = (pp.CaselessLiteral("RED")
                    | pp.CaselessLiteral("GREEN")
                    | pp.CaselessLiteral("BLUE"))[...],
            text = "red Green BluE blue GREEN green rEd",
            expected_list = ['RED', 'GREEN', 'BLUE', 'BLUE', 'GREEN', 'GREEN', 'RED'],
        ),
    ]

class TestWord(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "Simple Word match",
            expr = pp.Word("xy"),
            text = "xxyxxyy",
            expected_list = ["xxyxxyy"],
        ),
        PpTestSpec(
            desc = "Simple Word match of two separate Words",
            expr = pp.Word("x") + pp.Word("y"),
            text = "xxxxxyy",
            expected_list = ["xxxxx", "yy"],
        ),
        PpTestSpec(
            desc = "Simple Word match of two separate Words - implicitly skips whitespace",
            expr = pp.Word("x") + pp.Word("y"),
            text = "xxxxx yy",
            expected_list = ["xxxxx", "yy"],
        ),
    ]

class TestCombine(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc="Parsing real numbers - fail, parsed numbers are in pieces",
            expr=(pp.Word(pp.nums) + '.' + pp.Word(pp.nums))[...],
            text="1.2 2.3 3.1416 98.6",
            expected_list=['1', '.', '2', '2', '.', '3', '3', '.', '1416', '98', '.', '6'],
        ),
        PpTestSpec(
            desc="Parsing real numbers - better, use Combine to combine multiple tokens into one",
            expr=pp.Combine(pp.Word(pp.nums) + '.' + pp.Word(pp.nums))[...],
            text="1.2 2.3 3.1416 98.6",
            expected_list=['1.2', '2.3', '3.1416', '98.6'],
        ),
    ]

class TestRepetition(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "Match several words",
            expr = (pp.Word("x") | pp.Word("y"))[...],
            text = "xxyxxyyxxyxyxxxy",
            expected_list = ['xx', 'y', 'xx', 'yy', 'xx', 'y', 'x', 'y', 'xxx', 'y'],
        ),
        PpTestSpec(
            desc = "Match several words, skipping whitespace",
            expr = (pp.Word("x") | pp.Word("y"))[...],
            text = "x x  y xxy yxx y xyx  xxy",
            expected_list = ['x', 'x', 'y', 'xx', 'y', 'y', 'xx', 'y', 'x', 'y', 'x', 'xx', 'y'],
        ),
        PpTestSpec(
            desc = "Match several words, skipping whitespace (old style)",
            expr = pp.OneOrMore(pp.Word("x") | pp.Word("y")),
            text = "x x  y xxy yxx y xyx  xxy",
            expected_list = ['x', 'x', 'y', 'xx', 'y', 'y', 'xx', 'y', 'x', 'y', 'x', 'xx', 'y'],
        ),
        PpTestSpec(
            desc = "Match words and numbers - show use of results names to collect types of tokens",
            expr = (pp.Word(pp.alphas)("alpha*")
                    | pp.pyparsing_common.integer("int*"))[...],
            text = "sdlfj23084ksdfs08234kjsdlfkjd0934",
            expected_list = ['sdlfj', 23084, 'ksdfs', 8234, 'kjsdlfkjd', 934],
            expected_dict = { 'alpha': ['sdlfj', 'ksdfs', 'kjsdlfkjd'], 'int': [23084, 8234, 934] }
        ),
        PpTestSpec(
            desc = "Using delimitedList (comma is the default delimiter)",
            expr = pp.delimitedList(pp.Word(pp.alphas)),
            text = "xxyx,xy,y,xxyx,yxx, xy",
            expected_list = ['xxyx', 'xy', 'y', 'xxyx', 'yxx', 'xy'],
        ),
        PpTestSpec(
            desc = "Using delimitedList, with ':' delimiter",
            expr = pp.delimitedList(pp.Word(pp.hexnums, exact=2), delim=':', combine=True),
            text = "0A:4B:73:21:FE:76",
            expected_list = ['0A:4B:73:21:FE:76'],
        ),
    ]

class TestResultsName(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "Match with results name",
            expr = pp.Literal("xyz").setResultsName("value"),
            text = "xyz",
            expected_dict = {'value': 'xyz'},
            expected_list = ['xyz'],
        ),
        PpTestSpec(
            desc = "Match with results name - using naming short-cut",
            expr = pp.Literal("xyz")("value"),
            text = "xyz",
            expected_dict = {'value': 'xyz'},
            expected_list = ['xyz'],
        ),
        PpTestSpec(
            desc = "Define multiple results names",
            expr = pp.Word(pp.alphas, pp.alphanums)("key") + '=' + pp.pyparsing_common.integer("value"),
            text = "range=5280",
            expected_dict = {'key': 'range', 'value': 5280},
            expected_list = ['range', '=', 5280],
        ),
    ]

class TestGroups(PyparsingExpressionTestCase):
    EQ = pp.Suppress('=')
    tests = [
        PpTestSpec(
            desc = "Define multiple results names in groups",
            expr = pp.Group(pp.Word(pp.alphas)("key")
                            + EQ
                            + pp.pyparsing_common.number("value"))[...],
            text = "range=5280 long=-138.52 lat=46.91",
            expected_list = [['range', 5280], ['long', -138.52], ['lat', 46.91]],
        ),
        PpTestSpec(
            desc = "Define multiple results names in groups - use Dict to define results names using parsed keys",
            expr = pp.Dict(pp.Group(pp.Word(pp.alphas)
                                    + EQ
                                    + pp.pyparsing_common.number)[...]),
            text = "range=5280 long=-138.52 lat=46.91",
            expected_list = [['range', 5280], ['long', -138.52], ['lat', 46.91]],
            expected_dict = {'lat': 46.91, 'long': -138.52, 'range': 5280}
        ),
        PpTestSpec(
            desc = "Define multiple value types",
            expr = pp.Dict(pp.Group(pp.Word(pp.alphas)
                                          + EQ
                                          + (pp.pyparsing_common.number | pp.oneOf("True False") | pp.QuotedString("'"))
                                        )[...]
                           ),
            text = "long=-122.47 lat=37.82 public=True name='Golden Gate Bridge'",
            expected_list = [['long', -122.47], ['lat', 37.82], ['public', 'True'], ['name', 'Golden Gate Bridge']],
            expected_dict = {'long': -122.47, 'lat': 37.82, 'public': 'True', 'name': 'Golden Gate Bridge'}
        ),
    ]

class TestParseAction(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc="Parsing real numbers - use parse action to convert to float at parse time",
            expr=pp.Combine(pp.Word(pp.nums) + '.' + pp.Word(pp.nums)).addParseAction(lambda t: float(t[0]))[...],
            text="1.2 2.3 3.1416 98.6",
            expected_list= [1.2, 2.3, 3.1416, 98.6], # note, these are now floats, not strs
        ),
        PpTestSpec(
            desc = "Match with numeric string converted to int",
            expr = pp.Word("0123456789").addParseAction(lambda t: int(t[0])),
            text = "12345",
            expected_list = [12345],  # note - result is type int, not str
        ),
        PpTestSpec(
            desc = "Use two parse actions to convert numeric string, then convert to datetime",
            expr = pp.Word(pp.nums).addParseAction(lambda t: int(t[0]),
                                                   lambda t: datetime.utcfromtimestamp(t[0])),
            text = "1537415628",
            expected_list = [datetime(2018, 9, 20, 3, 53, 48)],
        ),
        PpTestSpec(
            desc = "Use tokenMap for parse actions that operate on a single-length token",
            expr = pp.Word(pp.nums).addParseAction(pp.tokenMap(int),
                                                   pp.tokenMap(datetime.utcfromtimestamp)),
            text = "1537415628",
            expected_list = [datetime(2018, 9, 20, 3, 53, 48)],
        ),
        PpTestSpec(
            desc = "Using a built-in function that takes a sequence of strs as a parse action",
            expr = pp.Word(pp.hexnums, exact=2)[...].addParseAction(':'.join),
            text = "0A4B7321FE76",
            expected_list = ['0A:4B:73:21:FE:76'],
        ),
        PpTestSpec(
            desc = "Using a built-in function that takes a sequence of strs as a parse action",
            expr = pp.Word(pp.hexnums, exact=2)[...].addParseAction(sorted),
            text = "0A4B7321FE76",
            expected_list = ['0A', '21', '4B', '73', '76', 'FE'],
        ),
    ]

class TestResultsModifyingParseAction(PyparsingExpressionTestCase):
    def compute_stats_parse_action(t):
        # by the time this parse action is called, parsed numeric words
        # have been converted to ints by a previous parse action, so
        # they can be treated as ints
        t['sum'] = sum(t)
        t['ave'] = sum(t) / len(t)
        t['min'] = min(t)
        t['max'] = max(t)

    tests = [
        PpTestSpec(
            desc = "A parse action that adds new key-values",
            expr = pp.pyparsing_common.integer[...].addParseAction(compute_stats_parse_action),
            text = "27 1 14 22 89",
            expected_list = [27, 1, 14, 22, 89],
            expected_dict = {'ave': 30.6, 'max': 89, 'min': 1, 'sum': 153}
        ),
    ]

class TestRegex(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc="Parsing real numbers - using Regex instead of Combine",
            expr=pp.Regex(r'\d+\.\d+').addParseAction(lambda t: float(t[0]))[...],
            text="1.2 2.3 3.1416 98.6",
            expected_list=[1.2, 2.3, 3.1416, 98.6],  # note, these are now floats, not strs
        ),
    ]

class TestParseCondition(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "Define a condition to only match numeric values that are multiples of 7",
            expr = pp.Word(pp.nums).addCondition(lambda t: int(t[0]) % 7 == 0)[...],
            text = "14 35 77 12 28",
            expected_list = ['14', '35', '77'],
        ),
        PpTestSpec(
            desc = "Separate conversion to int and condition into separate parse action/conditions",
            expr = pp.Word(pp.nums).addParseAction(lambda t: int(t[0]))
                                   .addCondition(lambda t: t[0] % 7 == 0)[...],
            text = "14 35 77 12 28",
            expected_list = [14, 35, 77],
        ),
    ]

class TestTransformStringUsingParseActions(PyparsingExpressionTestCase):
    markup_convert_map = {
        '*' : 'B',
        '_' : 'U',
        '/' : 'I',
    }
    def markup_convert(t):
        htmltag = TestTransformStringUsingParseActions.markup_convert_map[t.markup_symbol]
        return "<{0}>{1}</{2}>".format(htmltag, t.body, htmltag)

    tests = [
        PpTestSpec(
            desc = "Use transformString to convert simple markup to HTML",
            expr = (pp.oneOf(markup_convert_map)('markup_symbol')
                    + "(" + pp.CharsNotIn(")")('body') + ")").addParseAction(markup_convert),
            text = "Show in *(bold), _(underscore), or /(italic) type",
            expected_list = ['Show in <B>bold</B>, <U>underscore</U>, or <I>italic</I> type'],
            parse_fn = 'transformString',
        ),
    ]

class TestCommonHelperExpressions(PyparsingExpressionTestCase):
    tests = [
        PpTestSpec(
            desc = "A comma-delimited list of words",
            expr = pp.delimitedList(pp.Word(pp.alphas)),
            text = "this, that, blah,foo,   bar",
            expected_list = ['this', 'that', 'blah', 'foo', 'bar'],
        ),
        PpTestSpec(
            desc = "A counted array of words",
            expr = pp.countedArray(pp.Word('ab'))[...],
            text = "2 aaa bbb 0 3 abab bbaa abbab",
            expected_list = [['aaa', 'bbb'], [], ['abab', 'bbaa', 'abbab']],
        ),
        PpTestSpec(
            desc = "skipping comments with ignore",
            expr = (pp.pyparsing_common.identifier('lhs')
                    + '='
                    + pp.pyparsing_common.fnumber('rhs')).ignore(pp.cppStyleComment),
            text = "abc_100 = /* value to be tested */ 3.1416",
            expected_list = ['abc_100', '=', 3.1416],
            expected_dict = {'lhs': 'abc_100', 'rhs': 3.1416},
        ),
        PpTestSpec(
            desc = "some pre-defined expressions in pyparsing_common, and building a dotted identifier with delimted_list",
            expr = (pp.pyparsing_common.number("id_num")
                    + pp.delimitedList(pp.pyparsing_common.identifier, '.', combine=True)("name")
                    + pp.pyparsing_common.ipv4_address("ip_address")
                    ),
            text = "1001 www.google.com 192.168.10.199",
            expected_list = [1001, 'www.google.com', '192.168.10.199'],
            expected_dict = {'id_num': 1001, 'name': 'www.google.com', 'ip_address': '192.168.10.199'},
        ),
        PpTestSpec(
            desc = "using oneOf (shortcut for Literal('a') | Literal('b') | Literal('c'))",
            expr = pp.oneOf("a b c")[...],
            text = "a b a b b a c c a b b",
            expected_list = ['a', 'b', 'a', 'b', 'b', 'a', 'c', 'c', 'a', 'b', 'b'],
        ),
        PpTestSpec(
            desc = "parsing nested parentheses",
            expr = pp.nestedExpr(),
            text = "(a b (c) d (e f g ()))",
            expected_list = [['a', 'b', ['c'], 'd', ['e', 'f', 'g', []]]],
        ),
        PpTestSpec(
            desc = "parsing nested braces",
            expr = (pp.Keyword('if')
                    + pp.nestedExpr()('condition')
                    + pp.nestedExpr('{', '}')('body')),
            text = 'if ((x == y) || !z) {printf("{}");}',
            expected_list = ['if', [['x', '==', 'y'], '||', '!z'], ['printf(', '"{}"', ');']],
            expected_dict = {'condition': [[['x', '==', 'y'], '||', '!z']],
                             'body': [['printf(', '"{}"', ');']]},
        ),
    ]


def _get_decl_line_no(cls):
    import inspect
    return inspect.getsourcelines(cls)[1]


# get all test case classes defined in this module and sort them by decl line no
test_case_classes = list(PyparsingExpressionTestCase.__subclasses__())
test_case_classes.sort(key=_get_decl_line_no)

# make into a suite and run it - this will run the tests in the same order
# they are declared in this module
#
# runnable from setup.py using "python setup.py test -s simple_unit_tests.suite"
#
suite = unittest.TestSuite(cls() for cls in test_case_classes)


# ============ MAIN ================

if __name__ == '__main__':
    import sys
    if sys.version_info[0] < 3:
        print("simple_unit_tests.py requires Python 3.x - exiting...")
        exit(0)

    result = unittest.TextTestRunner().run(suite)

    exit(0 if result.wasSuccessful() else 1)
