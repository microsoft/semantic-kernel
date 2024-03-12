#
# idlparse.py
#
# an example of using the parsing module to be able to process a subset of the CORBA IDL grammar
#
# Copyright (c) 2003, Paul McGuire
#

from pyparsing import Literal, Word, OneOrMore, ZeroOrMore, \
        Forward, delimitedList, Group, Optional, alphas, restOfLine, cStyleComment, \
        alphanums, quotedString, ParseException, Keyword, Regex
import pprint
#~ import tree2image

bnf = None
def CORBA_IDL_BNF():
    global bnf

    if not bnf:

        # punctuation
        (colon,lbrace,rbrace,lbrack,rbrack,lparen,rparen,
        equals,comma,dot,slash,bslash,star,semi,langle,rangle) = map(Literal, r":{}[]()=,./\*;<>")

        # keywords
        (any_, attribute_, boolean_, case_, char_, const_, context_, default_, double_, enum_, exception_,
        FALSE_, fixed_, float_, inout_, interface_, in_, long_, module_, Object_, octet_, oneway_, out_, raises_,
        readonly_, sequence_, short_, string_, struct_, switch_, TRUE_, typedef_, unsigned_, union_, void_,
        wchar_, wstring_) = map(Keyword, """any attribute boolean case char const context
            default double enum exception FALSE fixed float inout interface in long module
            Object octet oneway out raises readonly sequence short string struct switch
            TRUE typedef unsigned union void wchar wstring""".split())

        identifier = Word( alphas, alphanums + "_" ).setName("identifier")

        real = Regex(r"[+-]?\d+\.\d*([Ee][+-]?\d+)?").setName("real")
        integer = Regex(r"0x[0-9a-fA-F]+|[+-]?\d+").setName("int")

        udTypeName = delimitedList( identifier, "::", combine=True ).setName("udType")
        typeName = ( any_ | boolean_ | char_ | double_ | fixed_ |
                    float_ | long_ | octet_ | short_ | string_ |
                    wchar_ | wstring_ | udTypeName ).setName("type")
        sequenceDef = Forward().setName("seq")
        sequenceDef << Group( sequence_ + langle + ( sequenceDef | typeName ) + rangle )
        typeDef = sequenceDef | ( typeName + Optional( lbrack + integer + rbrack ) )
        typedefDef = Group( typedef_ + typeDef + identifier + semi ).setName("typedef")

        moduleDef = Forward()
        constDef = Group( const_ + typeDef + identifier + equals + ( real | integer | quotedString ) + semi ) #| quotedString )
        exceptionItem = Group( typeDef + identifier + semi )
        exceptionDef = ( exception_ + identifier + lbrace + ZeroOrMore( exceptionItem ) + rbrace + semi )
        attributeDef = Optional( readonly_ ) + attribute_ + typeDef + identifier + semi
        paramlist = delimitedList( Group( ( inout_ | in_ | out_ ) + typeName + identifier ) ).setName( "paramlist" )
        operationDef = ( ( void_ ^ typeDef ) + identifier + lparen + Optional( paramlist ) + rparen + \
                        Optional( raises_ + lparen + Group( delimitedList( typeName ) ) + rparen ) + semi )
        interfaceItem = ( constDef | exceptionDef | attributeDef | operationDef )
        interfaceDef = Group( interface_ + identifier  + Optional( colon + delimitedList( typeName ) ) + lbrace + \
                        ZeroOrMore( interfaceItem ) + rbrace + semi ).setName("opnDef")
        moduleItem = ( interfaceDef | exceptionDef | constDef | typedefDef | moduleDef )
        moduleDef << module_ + identifier + lbrace + ZeroOrMore( moduleItem ) + rbrace + semi

        bnf = ( moduleDef | OneOrMore( moduleItem ) )

        singleLineComment = "//" + restOfLine
        bnf.ignore( singleLineComment )
        bnf.ignore( cStyleComment )

    return bnf

testnum = 1
def test( strng ):
    global testnum
    print(strng)
    try:
        bnf = CORBA_IDL_BNF()
        tokens = bnf.parseString( strng )
        print("tokens = ")
        pprint.pprint( tokens.asList() )
        imgname = "idlParse%02d.bmp" % testnum
        testnum += 1
        #~ tree2image.str2image( str(tokens.asList()), imgname )
    except ParseException as err:
        print(err.line)
        print(" "*(err.column-1) + "^")
        print(err)
    print()

if __name__ == "__main__":
    test(
        """
        /*
         * a block comment *
         */
        typedef string[10] tenStrings;
        typedef sequence<string> stringSeq;
        typedef sequence< sequence<string> > stringSeqSeq;

        interface QoSAdmin {
            stringSeq method1( in string arg1, inout long arg2 );
            stringSeqSeq method2( in string arg1, inout long arg2, inout long arg3);
            string method3();
          };
        """
        )
    test(
        """
        /*
         * a block comment *
         */
        typedef string[10] tenStrings;
        typedef
            /** ** *** **** *
             * a block comment *
             */
            sequence<string> /*comment inside an And */ stringSeq;
        /* */  /**/ /***/ /****/
        typedef sequence< sequence<string> > stringSeqSeq;

        interface QoSAdmin {
            stringSeq method1( in string arg1, inout long arg2 );
            stringSeqSeq method2( in string arg1, inout long arg2, inout long arg3);
            string method3();
          };
        """
        )
    test(
        r"""
          const string test="Test String\n";
          const long  a = 0;
          const long  b = -100;
          const float c = 3.14159;
          const long  d = 0x007f7f7f;
          exception TestException
            {
            string msg;
            sequence<string> dataStrings;
            };

          interface TestInterface
            {
            void method1( in string arg1, inout long arg2 );
            };
        """
        )
    test(
        """
        module Test1
          {
          exception TestException
            {
            string msg;
            ];

          interface TestInterface
            {
            void method1( in string arg1, inout long arg2 )
              raises ( TestException );
            };
          };
        """
        )
    test(
        """
        module Test1
          {
          exception TestException
            {
            string msg;
            };

          };
        """
        )
