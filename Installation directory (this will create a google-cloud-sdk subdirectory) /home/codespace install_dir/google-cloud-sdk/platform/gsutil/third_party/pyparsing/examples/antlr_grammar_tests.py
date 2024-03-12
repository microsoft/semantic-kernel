'''
Created on 4 sept. 2010

@author: luca

Submitted by Luca DallOlio, September, 2010
'''
import unittest
from . import antlr_grammar

class Test(unittest.TestCase):


    def testOptionsSpec(self):
        text = """options {
                            language = Python;
                        }"""
        antlr_grammar.optionsSpec.parseString(text) #@UndefinedVariable

    def testTokensSpec(self):
        text = """tokens {
                            PLUS     = '+' ;
                            MINUS    = '-' ;
                            MULT    = '*' ;
                            DIV    = '/' ;
                        }"""
        antlr_grammar.tokensSpec.parseString(text) #@UndefinedVariable

    def testBlock(self):
        text = """( PLUS | MINUS )"""
        antlr_grammar.block.parseString(text) #@UndefinedVariable

    def testRule(self):
        text = """expr    : term ( ( PLUS | MINUS )  term )* ;"""
        antlr_grammar.rule.parseString(text) #@UndefinedVariable

    def testLexerRule(self):
        text = """fragment DIGIT    : '0'..'9' ;"""
        antlr_grammar.rule.parseString(text) #@UndefinedVariable

    def testLexerRule2(self):
        text = """WHITESPACE : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+     { $channel = HIDDEN; } ;"""
        #antlr_grammar.rule.parseString(text) #@UndefinedVariable

    def testGrammar(self):
        text = """grammar SimpleCalc;

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

fragment DIGIT    : '0'..'9' ;"""
        antlrGrammarTree = antlr_grammar.grammarDef.parseString(text) #@UndefinedVariable
        pyparsingRules = antlr_grammar.antlrConverter(antlrGrammarTree)
        pyparsingRule = pyparsingRules["expr"]
        pyparsingTree = pyparsingRule.parseString("2 - 5 * 42 + 7 / 25")
        pyparsingTreeList = pyparsingTree.asList()
        print(pyparsingTreeList)
        self.assertEqual(pyparsingTreeList,
                         [[[['2'], []], [['-', [['5'], [['*', ['4', '2']]]]], ['+', [['7'], [['/', ['2', '5']]]]]]]]
                         )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testOptionsSpec']
    unittest.main()
