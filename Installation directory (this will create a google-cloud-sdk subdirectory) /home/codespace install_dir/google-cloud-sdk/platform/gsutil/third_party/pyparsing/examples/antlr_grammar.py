'''
antlr_grammar.py

Created on 4 sept. 2010

@author: luca

Submitted by Luca DallOlio, September, 2010
(Minor updates by Paul McGuire, June, 2012)
(Code idiom updates by Paul McGuire, April, 2019)
'''
from pyparsing import (Word, ZeroOrMore, printables, Suppress, OneOrMore, Group,
    LineEnd, Optional, White, originalTextFor, hexnums, nums, Combine, Literal, Keyword,
    cStyleComment, Regex, Forward, MatchFirst, And, oneOf, alphas, alphanums,
    delimitedList, Char)

# http://www.antlr.org/grammar/ANTLR/ANTLRv3.g

QUOTE,APOS,EQ,LBRACK,RBRACK,LBRACE,RBRACE,LPAR,RPAR,ROOT,BANG,AT,TIL,SEMI,COLON,VERT = map(Suppress,
                                                                                           '"\'=[]{}()^!@~;:|')
BSLASH = Literal('\\')
keywords = (SRC_, SCOPE_, OPTIONS_, TOKENS_, FRAGMENT, ID, LEXER, PARSER, GRAMMAR, TREE, CATCH, FINALLY,
            THROWS, PROTECTED, PUBLIC, PRIVATE, ) = map(Keyword,
    """src scope options tokens fragment id lexer parser grammar tree catch finally throws protected 
       public private """.split())
KEYWORD = MatchFirst(keywords)

# Tokens
EOL = Suppress(LineEnd()) # $
SGL_PRINTABLE = Char(printables)
singleTextString = originalTextFor(ZeroOrMore(~EOL + (White(" \t") | Word(printables)))).leaveWhitespace()
XDIGIT = hexnums
INT = Word(nums)
ESC = BSLASH + (oneOf(list(r'nrtbf\">'+"'")) | ('u' + Word(hexnums, exact=4)) | SGL_PRINTABLE)
LITERAL_CHAR = ESC | ~(APOS | BSLASH) + SGL_PRINTABLE
CHAR_LITERAL = APOS + LITERAL_CHAR + APOS
STRING_LITERAL = APOS + Combine(OneOrMore(LITERAL_CHAR)) + APOS
DOUBLE_QUOTE_STRING_LITERAL = '"' + ZeroOrMore(LITERAL_CHAR) + '"'
DOUBLE_ANGLE_STRING_LITERAL = '<<' + ZeroOrMore(SGL_PRINTABLE) + '>>'
TOKEN_REF = Word(alphas.upper(), alphanums+'_')
RULE_REF = Word(alphas.lower(), alphanums+'_')
ACTION_ESC = (BSLASH.suppress() + APOS
             | BSLASH.suppress()
             | BSLASH.suppress() + (~(APOS | QUOTE) + SGL_PRINTABLE)
              )
ACTION_CHAR_LITERAL = (APOS + (ACTION_ESC | ~(BSLASH | APOS) + SGL_PRINTABLE) + APOS)
ACTION_STRING_LITERAL = (QUOTE + ZeroOrMore(ACTION_ESC | ~(BSLASH | QUOTE) + SGL_PRINTABLE) + QUOTE)

SRC = SRC_.suppress() + ACTION_STRING_LITERAL("file") + INT("line")
id = TOKEN_REF | RULE_REF
SL_COMMENT = Suppress('//') + Suppress('$ANTLR') + SRC | ZeroOrMore(~EOL + Word(printables)) + EOL
ML_COMMENT = cStyleComment
WS = OneOrMore(Suppress(' ') | Suppress('\t') | (Optional(Suppress('\r')) + Literal('\n')))
WS_LOOP = ZeroOrMore(SL_COMMENT | ML_COMMENT)
NESTED_ARG_ACTION = Forward()
NESTED_ARG_ACTION << (LBRACK
                      + ZeroOrMore(NESTED_ARG_ACTION
                                   | ACTION_STRING_LITERAL
                                   | ACTION_CHAR_LITERAL)
                      + RBRACK)
ARG_ACTION = NESTED_ARG_ACTION
NESTED_ACTION = Forward()
NESTED_ACTION << (LBRACE
                  + ZeroOrMore(NESTED_ACTION
                               | SL_COMMENT
                               | ML_COMMENT
                               | ACTION_STRING_LITERAL
                               | ACTION_CHAR_LITERAL)
                  + RBRACE)
ACTION = NESTED_ACTION + Optional('?')
SCOPE = SCOPE_.suppress()
OPTIONS = OPTIONS_.suppress() + LBRACE # + WS_LOOP + Suppress('{')
TOKENS = TOKENS_.suppress() + LBRACE # + WS_LOOP + Suppress('{')
TREE_BEGIN = ROOT + LPAR
RANGE = Suppress('..')
REWRITE = Suppress('->')

# General Parser Definitions

# Grammar heading
optionValue = id | STRING_LITERAL | CHAR_LITERAL | INT | Literal('*').setName("s")

option = Group(id("id") + EQ + optionValue("value"))("option")
optionsSpec = OPTIONS + Group(OneOrMore(option + SEMI))("options") + RBRACE
tokenSpec = Group(TOKEN_REF("token_ref")
                  + (EQ + (STRING_LITERAL | CHAR_LITERAL)("lit")))("token") + SEMI
tokensSpec = TOKENS + Group(OneOrMore(tokenSpec))("tokens") + RBRACE
attrScope = SCOPE_.suppress() + id + ACTION
grammarType = LEXER + PARSER + TREE
actionScopeName = id | LEXER("l") | PARSER("p")
action = AT + Optional(actionScopeName + Suppress('::')) + id + ACTION

grammarHeading = (Optional(ML_COMMENT("ML_COMMENT"))
                  + Optional(grammarType)
                  + GRAMMAR
                  + id("grammarName") + SEMI
                  + Optional(optionsSpec)
                  + Optional(tokensSpec)
                  + ZeroOrMore(attrScope)
                  + ZeroOrMore(action))

modifier = PROTECTED | PUBLIC | PRIVATE | FRAGMENT
ruleAction = AT + id + ACTION
throwsSpec = THROWS.suppress() + delimitedList(id)
ruleScopeSpec = ((SCOPE_.suppress() + ACTION)
                 | (SCOPE_.suppress() + delimitedList(id) + SEMI)
                 | (SCOPE_.suppress() + ACTION + SCOPE_.suppress() + delimitedList(id) + SEMI))
unary_op = oneOf("^ !")
notTerminal = CHAR_LITERAL | TOKEN_REF | STRING_LITERAL
terminal = (CHAR_LITERAL | TOKEN_REF + Optional(ARG_ACTION) | STRING_LITERAL | '.') + Optional(unary_op)
block = Forward()
notSet = TIL + (notTerminal | block)
rangeNotPython = CHAR_LITERAL("c1") + RANGE + CHAR_LITERAL("c2")
atom = Group((rangeNotPython + Optional(unary_op)("op"))
             | terminal
             | (notSet + Optional(unary_op)("op"))
             | (RULE_REF + Optional(ARG_ACTION("arg")) + Optional(unary_op)("op"))
             )
element = Forward()
treeSpec = ROOT + LPAR + element*(2,) + RPAR
ebnfSuffix = oneOf("? * +")
ebnf = block + Optional(ebnfSuffix("op") | '=>')
elementNoOptionSpec = ((id("result_name")  + oneOf('= +=')("labelOp")  + atom("atom") + Optional(ebnfSuffix))
                       | (id("result_name") + oneOf('= +=')("labelOp") + block + Optional(ebnfSuffix))
                       | atom("atom") + Optional(ebnfSuffix)
                       | ebnf
                       | ACTION
                       | (treeSpec + Optional(ebnfSuffix))
                       ) # |   SEMPRED ( '=>' -> GATED_SEMPRED | -> SEMPRED )
element <<= Group(elementNoOptionSpec)("element")
# Do not ask me why group is needed twice... seems like the xml that you see is not always the real structure?
alternative = Group(Group(OneOrMore(element))("elements"))
rewrite = Optional(Literal('TODO REWRITE RULES TODO'))
block <<= (LPAR
           + Optional(Optional(optionsSpec("opts")) + COLON)
           + Group(alternative('a1')
                   + rewrite
                   + Group(ZeroOrMore(VERT
                                      + alternative('a2')
                                      + rewrite))("alternatives"))("block")
           + RPAR)
altList = alternative('a1') + rewrite + Group(ZeroOrMore(VERT + alternative('a2') + rewrite))("alternatives")
exceptionHandler = CATCH.suppress() + ARG_ACTION + ACTION
finallyClause = FINALLY.suppress() + ACTION
exceptionGroup = (OneOrMore(exceptionHandler) + Optional(finallyClause)) | finallyClause

ruleHeading = (Optional(ML_COMMENT)("ruleComment")
               + Optional(modifier)("modifier")
               + id("ruleName")
               + Optional("!")
               + Optional(ARG_ACTION("arg"))
               + Optional(Suppress('returns') + ARG_ACTION("rt"))
               + Optional(throwsSpec)
               + Optional(optionsSpec)
               + Optional(ruleScopeSpec)
               + ZeroOrMore(ruleAction))
rule = Group(ruleHeading + COLON + altList + SEMI + Optional(exceptionGroup))("rule")

grammarDef = grammarHeading + Group(OneOrMore(rule))("rules")

def grammar():
    return grammarDef

def __antlrAlternativesConverter(pyparsingRules, antlrBlock):
    rule = None
    if hasattr(antlrBlock, 'alternatives') and antlrBlock.alternatives != '' and len(antlrBlock.alternatives) > 0:
        alternatives = []
        alternatives.append(__antlrAlternativeConverter(pyparsingRules, antlrBlock.a1))
        for alternative in antlrBlock.alternatives:
            alternatives.append(__antlrAlternativeConverter(pyparsingRules, alternative))
        rule = MatchFirst(alternatives)("anonymous_or")
    elif hasattr(antlrBlock, 'a1') and antlrBlock.a1 != '':
        rule = __antlrAlternativeConverter(pyparsingRules, antlrBlock.a1)
    else:
        raise Exception('Not yet implemented')
    assert rule != None
    return rule

def __antlrAlternativeConverter(pyparsingRules, antlrAlternative):
    elementList = []
    for element in antlrAlternative.elements:
        rule = None
        if hasattr(element.atom, 'c1') and element.atom.c1 != '':
            regex = r'['+str(element.atom.c1[0])+'-'+str(element.atom.c2[0]+']')
            rule = Regex(regex)("anonymous_regex")
        elif hasattr(element, 'block') and element.block != '':
            rule = __antlrAlternativesConverter(pyparsingRules, element.block)
        else:
            ruleRef = element.atom[0]
            assert ruleRef in pyparsingRules
            rule = pyparsingRules[ruleRef](ruleRef)
        if hasattr(element, 'op') and element.op != '':
            if element.op == '+':
                rule = Group(OneOrMore(rule))("anonymous_one_or_more")
            elif element.op == '*':
                rule = Group(ZeroOrMore(rule))("anonymous_zero_or_more")
            elif element.op == '?':
                rule = Optional(rule)
            else:
                raise Exception('rule operator not yet implemented : ' + element.op)
        rule = rule
        elementList.append(rule)
    if len(elementList) > 1:
        rule = Group(And(elementList))("anonymous_and")
    else:
        rule = elementList[0]
    assert rule is not None
    return rule

def __antlrRuleConverter(pyparsingRules, antlrRule):
    rule = None
    rule = __antlrAlternativesConverter(pyparsingRules, antlrRule)
    assert rule != None
    rule(antlrRule.ruleName)
    return rule

def antlrConverter(antlrGrammarTree):
    pyparsingRules = {}

    antlrTokens = {}
    for antlrToken in antlrGrammarTree.tokens:
        antlrTokens[antlrToken.token_ref] = antlrToken.lit
    for antlrTokenName, antlrToken in list(antlrTokens.items()):
        pyparsingRules[antlrTokenName] = Literal(antlrToken)

    antlrRules = {}
    for antlrRule in antlrGrammarTree.rules:
        antlrRules[antlrRule.ruleName] = antlrRule
        pyparsingRules[antlrRule.ruleName] = Forward() # antlr is a top down grammar
    for antlrRuleName, antlrRule in list(antlrRules.items()):
        pyparsingRule = __antlrRuleConverter(pyparsingRules, antlrRule)
        assert pyparsingRule != None
        pyparsingRules[antlrRuleName] <<= pyparsingRule

    return pyparsingRules

if __name__ == "__main__":

    text = """\
grammar SimpleCalc;

options {
    language = Python;
}

tokens {
    PLUS     = '+' ;
    MINUS    = '-' ;
    MULT    = '*' ;
    DIV    = '/' ;
}

/*------------------------------------------------------------------
 * PARSER RULES
 *------------------------------------------------------------------*/

expr    : term ( ( PLUS | MINUS )  term )* ;

term    : factor ( ( MULT | DIV ) factor )* ;

factor    : NUMBER ;


/*------------------------------------------------------------------
 * LEXER RULES
 *------------------------------------------------------------------*/

NUMBER    : (DIGIT)+ ;

/* WHITESPACE : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+     { $channel = HIDDEN; } ; */

fragment DIGIT    : '0'..'9' ;

"""

    grammar().validate()
    antlrGrammarTree = grammar().parseString(text)
    print(antlrGrammarTree.dump())
    pyparsingRules = antlrConverter(antlrGrammarTree)
    pyparsingRule = pyparsingRules["expr"]
    pyparsingTree = pyparsingRule.parseString("2 - 5 * 42 + 7 / 25")
    print(pyparsingTree.dump())
