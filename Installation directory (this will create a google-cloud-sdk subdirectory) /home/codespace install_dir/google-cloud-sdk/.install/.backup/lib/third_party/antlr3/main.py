"""ANTLR3 runtime package"""

# begin[licence]
#
# [The "BSD licence"]
# Copyright (c) 2005-2008 Terence Parr
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# end[licence]


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import optparse
import sys

import antlr3
from six.moves import input


class _Main(object):

  def __init__(self):
    self.stdin = sys.stdin
    self.stdout = sys.stdout
    self.stderr = sys.stderr

  def parseOptions(self, argv):
    optParser = optparse.OptionParser()
    optParser.add_option(
        "--encoding", action="store", type="string", dest="encoding")
    optParser.add_option("--input", action="store", type="string", dest="input")
    optParser.add_option(
        "--interactive", "-i", action="store_true", dest="interactive")
    optParser.add_option("--no-output", action="store_true", dest="no_output")
    optParser.add_option("--profile", action="store_true", dest="profile")
    optParser.add_option("--hotshot", action="store_true", dest="hotshot")

    self.setupOptions(optParser)

    return optParser.parse_args(argv[1:])

  def setupOptions(self, optParser):
    pass

  def execute(self, argv):
    options, args = self.parseOptions(argv)

    self.setUp(options)

    if options.interactive:
      while True:
        try:
          input = input(">>> ")
        except (EOFError, KeyboardInterrupt):
          self.stdout.write("\nBye.\n")
          break

        inStream = antlr3.ANTLRStringStream(input)
        self.parseStream(options, inStream)

    else:
      if options.input is not None:
        inStream = antlr3.ANTLRStringStream(options.input)

      elif len(args) == 1 and args[0] != "-":
        inStream = antlr3.ANTLRFileStream(args[0], encoding=options.encoding)

      else:
        inStream = antlr3.ANTLRInputStream(
            self.stdin, encoding=options.encoding)

      if options.profile:
        try:
          import cProfile as profile
        except ImportError:
          import profile

        profile.runctx("self.parseStream(options, inStream)", globals(),
                       locals(), "profile.dat")

        import pstats
        stats = pstats.Stats("profile.dat")
        stats.strip_dirs()
        stats.sort_stats("time")
        stats.print_stats(100)

      elif options.hotshot:
        import hotshot

        profiler = hotshot.Profile("hotshot.dat")
        profiler.runctx("self.parseStream(options, inStream)", globals(),
                        locals())

      else:
        self.parseStream(options, inStream)

  def setUp(self, options):
    pass

  def parseStream(self, options, inStream):
    raise NotImplementedError

  def write(self, options, text):
    if not options.no_output:
      self.stdout.write(text)

  def writeln(self, options, text):
    self.write(options, text + "\n")


class LexerMain(_Main):

  def __init__(self, lexerClass):
    _Main.__init__(self)

    self.lexerClass = lexerClass

  def parseStream(self, options, inStream):
    lexer = self.lexerClass(inStream)
    for token in lexer:
      self.writeln(options, str(token))


class ParserMain(_Main):

  def __init__(self, lexerClassName, parserClass):
    _Main.__init__(self)

    self.lexerClassName = lexerClassName
    self.lexerClass = None
    self.parserClass = parserClass

  def setupOptions(self, optParser):
    optParser.add_option(
        "--lexer",
        action="store",
        type="string",
        dest="lexerClass",
        default=self.lexerClassName)
    optParser.add_option(
        "--rule", action="store", type="string", dest="parserRule")

  def setUp(self, options):
    lexerMod = __import__(options.lexerClass)
    self.lexerClass = getattr(lexerMod, options.lexerClass)

  def parseStream(self, options, inStream):
    lexer = self.lexerClass(inStream)
    tokenStream = antlr3.CommonTokenStream(lexer)
    parser = self.parserClass(tokenStream)
    result = getattr(parser, options.parserRule)()
    if result is not None:
      if hasattr(result, "tree"):
        if result.tree is not None:
          self.writeln(options, result.tree.toStringTree())
      else:
        self.writeln(options, repr(result))


class WalkerMain(_Main):

  def __init__(self, walkerClass):
    _Main.__init__(self)

    self.lexerClass = None
    self.parserClass = None
    self.walkerClass = walkerClass

  def setupOptions(self, optParser):
    optParser.add_option(
        "--lexer",
        action="store",
        type="string",
        dest="lexerClass",
        default=None)
    optParser.add_option(
        "--parser",
        action="store",
        type="string",
        dest="parserClass",
        default=None)
    optParser.add_option(
        "--parser-rule",
        action="store",
        type="string",
        dest="parserRule",
        default=None)
    optParser.add_option(
        "--rule", action="store", type="string", dest="walkerRule")

  def setUp(self, options):
    lexerMod = __import__(options.lexerClass)
    self.lexerClass = getattr(lexerMod, options.lexerClass)
    parserMod = __import__(options.parserClass)
    self.parserClass = getattr(parserMod, options.parserClass)

  def parseStream(self, options, inStream):
    lexer = self.lexerClass(inStream)
    tokenStream = antlr3.CommonTokenStream(lexer)
    parser = self.parserClass(tokenStream)
    result = getattr(parser, options.parserRule)()
    if result is not None:
      assert hasattr(result, "tree"), "Parser did not return an AST"
      nodeStream = antlr3.tree.CommonTreeNodeStream(result.tree)
      nodeStream.setTokenStream(tokenStream)
      walker = self.walkerClass(nodeStream)
      result = getattr(walker, options.walkerRule)()
      if result is not None:
        if hasattr(result, "tree"):
          self.writeln(options, result.tree.toStringTree())
        else:
          self.writeln(options, repr(result))
