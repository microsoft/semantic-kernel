# protobuf_parser.py
#
#  simple parser for parsing protobuf .proto files
#
#  Copyright 2010, Paul McGuire
#

from pyparsing import (Word, alphas, alphanums, Regex, Suppress, Forward,
    Keyword, Group, oneOf, ZeroOrMore, Optional, delimitedList,
    restOfLine, quotedString, Dict)

ident = Word(alphas+"_",alphanums+"_").setName("identifier")
integer = Regex(r"[+-]?\d+")

LBRACE,RBRACE,LBRACK,RBRACK,LPAR,RPAR,EQ,SEMI = map(Suppress,"{}[]()=;")

kwds = """message required optional repeated enum extensions extends extend
          to package service rpc returns true false option import"""
for kw in kwds.split():
    exec("{0}_ = Keyword('{1}')".format(kw.upper(), kw))

messageBody = Forward()

messageDefn = MESSAGE_ - ident("messageId") + LBRACE + messageBody("body") + RBRACE

typespec = oneOf("""double float int32 int64 uint32 uint64 sint32 sint64
                    fixed32 fixed64 sfixed32 sfixed64 bool string bytes""") | ident
rvalue = integer | TRUE_ | FALSE_ | ident
fieldDirective = LBRACK + Group(ident + EQ + rvalue) + RBRACK
fieldDefn = (( REQUIRED_ | OPTIONAL_ | REPEATED_ )("fieldQualifier") -
              typespec("typespec") + ident("ident") + EQ + integer("fieldint") + ZeroOrMore(fieldDirective) + SEMI)

# enumDefn ::= 'enum' ident '{' { ident '=' integer ';' }* '}'
enumDefn = ENUM_("typespec") - ident('name') + LBRACE + Dict( ZeroOrMore( Group(ident + EQ + integer + SEMI) ))('values') + RBRACE

# extensionsDefn ::= 'extensions' integer 'to' integer ';'
extensionsDefn = EXTENSIONS_ - integer + TO_ + integer + SEMI

# messageExtension ::= 'extend' ident '{' messageBody '}'
messageExtension = EXTEND_ - ident + LBRACE + messageBody + RBRACE

# messageBody ::= { fieldDefn | enumDefn | messageDefn | extensionsDefn | messageExtension }*
messageBody << Group(ZeroOrMore( Group(fieldDefn | enumDefn | messageDefn | extensionsDefn | messageExtension) ))

# methodDefn ::= 'rpc' ident '(' [ ident ] ')' 'returns' '(' [ ident ] ')' ';'
methodDefn = (RPC_ - ident("methodName") +
              LPAR + Optional(ident("methodParam")) + RPAR +
              RETURNS_ + LPAR + Optional(ident("methodReturn")) + RPAR)

# serviceDefn ::= 'service' ident '{' methodDefn* '}'
serviceDefn = SERVICE_ - ident("serviceName") + LBRACE + ZeroOrMore(Group(methodDefn)) + RBRACE

# packageDirective ::= 'package' ident [ '.' ident]* ';'
packageDirective = Group(PACKAGE_ - delimitedList(ident, '.', combine=True) + SEMI)

comment = '//' + restOfLine

importDirective = IMPORT_ - quotedString("importFileSpec") + SEMI

optionDirective = OPTION_ - ident("optionName") + EQ + quotedString("optionValue") + SEMI

topLevelStatement = Group(messageDefn | messageExtension | enumDefn | serviceDefn | importDirective | optionDirective)

parser = Optional(packageDirective) + ZeroOrMore(topLevelStatement)

parser.ignore(comment)


test1 = """message Person {
  required int32 id = 1;
  required string name = 2;
  optional string email = 3;
}"""

test2 = """package tutorial;

message Person {
  required string name = 1;
  required int32 id = 2;
  optional string email = 3;

  enum PhoneType {
    MOBILE = 0;
    HOME = 1;
    WORK = 2;
  }

  message PhoneNumber {
    required string number = 1;
    optional PhoneType type = 2 [default = HOME];
  }

  repeated PhoneNumber phone = 4;
}

message AddressBook {
  repeated Person person = 1;
}"""

parser.runTests([test1, test2])
