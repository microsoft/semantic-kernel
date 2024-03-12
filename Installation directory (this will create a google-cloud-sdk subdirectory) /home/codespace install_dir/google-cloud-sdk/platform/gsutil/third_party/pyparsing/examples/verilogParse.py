#
# verilogParse.py
#
# an example of using the pyparsing module to be able to process Verilog files
# uses BNF defined at http://www.verilog.com/VerilogBNF.html
#
#    Copyright (c) 2004-2011 Paul T. McGuire.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# If you find this software to be useful, please make a donation to one
# of the following charities:
# - the Red Cross (https://www.redcross.org/)
# - Hospice Austin (https://www.hospiceaustin.org/)
#
#    DISCLAIMER:
#    THIS SOFTWARE IS PROVIDED BY PAUL T. McGUIRE ``AS IS'' AND ANY EXPRESS OR
#    IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#    MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO
#    EVENT SHALL PAUL T. McGUIRE OR CO-CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#    INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#    BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OFUSE,
#    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
#    OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
#    EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#    For questions or inquiries regarding this license, or commercial use of
#    this software, contact the author via e-mail: ptmcg@users.sourceforge.net
#
# Todo:
#  - add pre-process pass to implement compilerDirectives (ifdef, include, etc.)
#
# Revision History:
#
#   1.0   - Initial release
#   1.0.1 - Fixed grammar errors:
#           . real declaration was incorrect
#           . tolerant of '=>' for '*>' operator
#           . tolerant of '?' as hex character
#           . proper handling of mintypmax_expr within path delays
#   1.0.2 - Performance tuning (requires pyparsing 1.3)
#   1.0.3 - Performance updates, using Regex (requires pyparsing 1.4)
#   1.0.4 - Performance updates, enable packrat parsing (requires pyparsing 1.4.2)
#   1.0.5 - Converted keyword Literals to Keywords, added more use of Group to
#           group parsed results tokens
#   1.0.6 - Added support for module header with no ports list (thanks, Thomas Dejanovic!)
#   1.0.7 - Fixed erroneous '<<' Forward definition in timCheckCond, omitting ()'s
#   1.0.8 - Re-released under MIT license
#   1.0.9 - Enhanced udpInstance to handle identifiers with leading '\' and subscripting
#   1.0.10 - Fixed change added in 1.0.9 to work for all identifiers, not just those used
#           for udpInstance.
#   1.0.11 - Fixed bug in inst_args, content alternatives were reversed
#
import time
import pprint
import sys

__version__ = "1.0.11"

from pyparsing import Literal, Keyword, Word, OneOrMore, ZeroOrMore, \
        Forward, delimitedList, Group, Optional, Combine, alphas, nums, restOfLine, \
        alphanums, dblQuotedString, empty, ParseException, oneOf, \
        StringEnd, FollowedBy, ParserElement, Regex, cppStyleComment
import pyparsing
usePackrat = False

packratOn = False

if usePackrat:
    try:
        ParserElement.enablePackrat()
    except Exception:
        pass
    else:
        packratOn = True

def dumpTokens(s,l,t):
    import pprint
    pprint.pprint( t.asList() )

verilogbnf = None
def Verilog_BNF():
    global verilogbnf

    if verilogbnf is None:

        # compiler directives
        compilerDirective = Combine( "`" + \
            oneOf("define undef ifdef else endif default_nettype "
                  "include resetall timescale unconnected_drive "
                  "nounconnected_drive celldefine endcelldefine") + \
            restOfLine ).setName("compilerDirective")

        # primitives
        SEMI,COLON,LPAR,RPAR,LBRACE,RBRACE,LBRACK,RBRACK,DOT,COMMA,EQ = map(Literal,";:(){}[].,=")

        identLead = alphas+"$_"
        identBody = alphanums+"$_"
        identifier1 = Regex( r"\.?["+identLead+"]["+identBody+r"]*(\.["+identLead+"]["+identBody+"]*)*"
                            ).setName("baseIdent")
        identifier2 = Regex(r"\\\S+").setParseAction(lambda t:t[0][1:]).setName("escapedIdent")#.setDebug()
        identifier = identifier1 | identifier2
        assert(identifier2 == r'\abc')

        hexnums = nums + "abcdefABCDEF" + "_?"
        base = Regex("'[bBoOdDhH]").setName("base")
        basedNumber = Combine( Optional( Word(nums + "_") ) + base + Word(hexnums+"xXzZ"),
                               joinString=" ", adjacent=False ).setName("basedNumber")
        #~ number = ( basedNumber | Combine( Word( "+-"+spacedNums, spacedNums ) +
                           #~ Optional( DOT + Optional( Word( spacedNums ) ) ) +
                           #~ Optional( e + Word( "+-"+spacedNums, spacedNums ) ) ).setName("numeric") )
        number = ( basedNumber | \
                   Regex(r"[+-]?[0-9_]+(\.[0-9_]*)?([Ee][+-]?[0-9_]+)?") \
                  ).setName("numeric")
        #~ decnums = nums + "_"
        #~ octnums = "01234567" + "_"
        expr = Forward().setName("expr")
        concat = Group( LBRACE + delimitedList( expr ) + RBRACE )
        multiConcat = Group("{" + expr + concat + "}").setName("multiConcat")
        funcCall = Group(identifier + LPAR + Optional( delimitedList( expr ) ) + RPAR).setName("funcCall")

        subscrRef = Group(LBRACK + delimitedList( expr, COLON ) + RBRACK)
        subscrIdentifier = Group( identifier + Optional( subscrRef ) )
        #~ scalarConst = "0" | (( FollowedBy('1') + oneOf("1'b0 1'b1 1'bx 1'bX 1'B0 1'B1 1'Bx 1'BX 1") ))
        scalarConst = Regex("0|1('[Bb][01xX])?")
        mintypmaxExpr = Group( expr + COLON + expr + COLON + expr ).setName("mintypmax")
        primary = (
                  number |
                  (LPAR + mintypmaxExpr + RPAR ) |
                  ( LPAR + Group(expr) + RPAR ).setName("nestedExpr") |
                  multiConcat |
                  concat |
                  dblQuotedString |
                  funcCall |
                  subscrIdentifier
                  )

        unop  = oneOf( "+  -  !  ~  &  ~&  |  ^|  ^  ~^" ).setName("unop")
        binop = oneOf( "+  -  *  /  %  ==  !=  ===  !==  &&  "
                       "||  <  <=  >  >=  &  |  ^  ^~  >>  << ** <<< >>>" ).setName("binop")

        expr << (
                ( unop + expr ) |  # must be first!
                ( primary + "?" + expr + COLON + expr ) |
                ( primary + Optional( binop + expr ) )
                )

        lvalue = subscrIdentifier | concat

        # keywords
        if_        = Keyword("if")
        else_      = Keyword("else")
        edge       = Keyword("edge")
        posedge    = Keyword("posedge")
        negedge    = Keyword("negedge")
        specify    = Keyword("specify")
        endspecify = Keyword("endspecify")
        fork       = Keyword("fork")
        join       = Keyword("join")
        begin      = Keyword("begin")
        end        = Keyword("end")
        default    = Keyword("default")
        forever    = Keyword("forever")
        repeat     = Keyword("repeat")
        while_     = Keyword("while")
        for_       = Keyword("for")
        case       = oneOf( "case casez casex" )
        endcase    = Keyword("endcase")
        wait       = Keyword("wait")
        disable    = Keyword("disable")
        deassign   = Keyword("deassign")
        force      = Keyword("force")
        release    = Keyword("release")
        assign     = Keyword("assign")

        eventExpr = Forward()
        eventTerm = ( posedge + expr ) | ( negedge + expr ) | expr | ( LPAR + eventExpr + RPAR )
        eventExpr << (
            Group( delimitedList( eventTerm, Keyword("or") ) )
            )
        eventControl = Group( "@" + ( ( LPAR + eventExpr + RPAR ) | identifier | "*" ) ).setName("eventCtrl")

        delayArg = ( number |
                     Word(alphanums+"$_") | #identifier |
                     ( LPAR + Group( delimitedList( mintypmaxExpr | expr ) ) + RPAR )
                   ).setName("delayArg")#.setDebug()
        delay = Group( "#" + delayArg ).setName("delay")#.setDebug()
        delayOrEventControl = delay | eventControl

        assgnmt   = Group( lvalue + EQ + Optional( delayOrEventControl ) + expr ).setName( "assgnmt" )
        nbAssgnmt = Group(( lvalue + "<=" + Optional( delay ) + expr ) |
                     ( lvalue + "<=" + Optional( eventControl ) + expr )).setName( "nbassgnmt" )

        range = LBRACK + expr + COLON + expr + RBRACK

        paramAssgnmt = Group( identifier + EQ + expr ).setName("paramAssgnmt")
        parameterDecl = Group( "parameter" + Optional( range ) + delimitedList( paramAssgnmt ) + SEMI).setName("paramDecl")

        inputDecl = Group( "input" + Optional( range ) + delimitedList( identifier ) + SEMI )
        outputDecl = Group( "output" + Optional( range ) + delimitedList( identifier ) + SEMI )
        inoutDecl = Group( "inout" + Optional( range ) + delimitedList( identifier ) + SEMI )

        regIdentifier = Group( identifier + Optional( LBRACK + expr + COLON + expr + RBRACK ) )
        regDecl = Group( "reg" + Optional("signed") + Optional( range ) + delimitedList( regIdentifier ) + SEMI ).setName("regDecl")
        timeDecl = Group( "time" + delimitedList( regIdentifier ) + SEMI )
        integerDecl = Group( "integer" + delimitedList( regIdentifier ) + SEMI )

        strength0 = oneOf("supply0  strong0  pull0  weak0  highz0")
        strength1 = oneOf("supply1  strong1  pull1  weak1  highz1")
        driveStrength = Group( LPAR + ( ( strength0 + COMMA + strength1 ) |
                                       ( strength1 + COMMA + strength0 ) ) + RPAR ).setName("driveStrength")
        nettype = oneOf("wire  tri  tri1  supply0  wand  triand  tri0  supply1  wor  trior  trireg")
        expandRange = Optional( oneOf("scalared vectored") ) + range
        realDecl = Group( "real" + delimitedList( identifier ) + SEMI )

        eventDecl = Group( "event" + delimitedList( identifier ) + SEMI )

        blockDecl = (
            parameterDecl |
            regDecl |
            integerDecl |
            realDecl |
            timeDecl |
            eventDecl
            )

        stmt = Forward().setName("stmt")#.setDebug()
        stmtOrNull = stmt | SEMI
        caseItem = ( delimitedList( expr ) + COLON + stmtOrNull ) | \
                   ( default + Optional(":") + stmtOrNull )
        stmt << Group(
            ( begin + Group( ZeroOrMore( stmt ) ) + end ).setName("begin-end") |
            ( if_ + Group(LPAR + expr + RPAR) + stmtOrNull + Optional( else_ + stmtOrNull ) ).setName("if") |
            ( delayOrEventControl + stmtOrNull ) |
            ( case + LPAR + expr + RPAR + OneOrMore( caseItem ) + endcase ) |
            ( forever + stmt ) |
            ( repeat + LPAR + expr + RPAR + stmt ) |
            ( while_ + LPAR + expr + RPAR + stmt ) |
            ( for_ + LPAR + assgnmt + SEMI + Group( expr ) + SEMI + assgnmt + RPAR + stmt ) |
            ( fork + ZeroOrMore( stmt ) + join ) |
            ( fork + COLON + identifier + ZeroOrMore( blockDecl ) + ZeroOrMore( stmt ) + end ) |
            ( wait + LPAR + expr + RPAR + stmtOrNull ) |
            ( "->" + identifier + SEMI ) |
            ( disable + identifier + SEMI ) |
            ( assign + assgnmt + SEMI ) |
            ( deassign + lvalue + SEMI ) |
            ( force + assgnmt + SEMI ) |
            ( release + lvalue + SEMI ) |
            ( begin + COLON + identifier + ZeroOrMore( blockDecl ) + ZeroOrMore( stmt ) + end ).setName("begin:label-end") |
            # these  *have* to go at the end of the list!!!
            ( assgnmt + SEMI ) |
            ( nbAssgnmt + SEMI ) |
            ( Combine( Optional("$") + identifier ) + Optional( LPAR + delimitedList(expr|empty) + RPAR ) + SEMI )
            ).setName("stmtBody")
        """
        x::=<blocking_assignment> ;
        x||= <non_blocking_assignment> ;
        x||= if ( <expression> ) <statement_or_null>
        x||= if ( <expression> ) <statement_or_null> else <statement_or_null>
        x||= case ( <expression> ) <case_item>+ endcase
        x||= casez ( <expression> ) <case_item>+ endcase
        x||= casex ( <expression> ) <case_item>+ endcase
        x||= forever <statement>
        x||= repeat ( <expression> ) <statement>
        x||= while ( <expression> ) <statement>
        x||= for ( <assignment> ; <expression> ; <assignment> ) <statement>
        x||= <delay_or_event_control> <statement_or_null>
        x||= wait ( <expression> ) <statement_or_null>
        x||= -> <name_of_event> ;
        x||= <seq_block>
        x||= <par_block>
        x||= <task_enable>
        x||= <system_task_enable>
        x||= disable <name_of_task> ;
        x||= disable <name_of_block> ;
        x||= assign <assignment> ;
        x||= deassign <lvalue> ;
        x||= force <assignment> ;
        x||= release <lvalue> ;
        """
        alwaysStmt = Group( "always" + Optional(eventControl) + stmt ).setName("alwaysStmt")
        initialStmt = Group( "initial" + stmt ).setName("initialStmt")

        chargeStrength = Group( LPAR + oneOf( "small medium large" ) + RPAR ).setName("chargeStrength")

        continuousAssign = Group(
            assign + Optional( driveStrength ) + Optional( delay ) + delimitedList( assgnmt ) + SEMI
            ).setName("continuousAssign")


        tfDecl = (
            parameterDecl |
            inputDecl |
            outputDecl |
            inoutDecl |
            regDecl |
            timeDecl |
            integerDecl |
            realDecl
            )

        functionDecl = Group(
            "function" + Optional( range | "integer" | "real" ) + identifier + SEMI +
            Group( OneOrMore( tfDecl ) ) +
            Group( ZeroOrMore( stmt ) ) +
            "endfunction"
            )

        inputOutput = oneOf("input output")
        netDecl1Arg = ( nettype +
            Optional( expandRange ) +
            Optional( delay ) +
            Group( delimitedList( ~inputOutput + identifier ) ) )
        netDecl2Arg = ( "trireg" +
            Optional( chargeStrength ) +
            Optional( expandRange ) +
            Optional( delay ) +
            Group( delimitedList( ~inputOutput + identifier ) ) )
        netDecl3Arg = ( nettype +
            Optional( driveStrength ) +
            Optional( expandRange ) +
            Optional( delay ) +
            Group( delimitedList( assgnmt ) ) )
        netDecl1 = Group(netDecl1Arg + SEMI).setName("netDecl1")
        netDecl2 = Group(netDecl2Arg + SEMI).setName("netDecl2")
        netDecl3 = Group(netDecl3Arg + SEMI).setName("netDecl3")

        gateType = oneOf("and  nand  or  nor xor  xnor buf  bufif0 bufif1 "
                         "not  notif0 notif1  pulldown pullup nmos  rnmos "
                         "pmos rpmos cmos rcmos   tran rtran  tranif0  "
                         "rtranif0  tranif1 rtranif1"  )
        gateInstance = Optional( Group( identifier + Optional( range ) ) ) + \
                        LPAR + Group( delimitedList( expr ) ) + RPAR
        gateDecl = Group( gateType +
            Optional( driveStrength ) +
            Optional( delay ) +
            delimitedList( gateInstance) +
            SEMI )

        udpInstance = Group( Group( identifier + Optional(range | subscrRef) ) +
            LPAR + Group( delimitedList( expr ) ) + RPAR )
        udpInstantiation = Group( identifier -
            Optional( driveStrength ) +
            Optional( delay ) +
            delimitedList( udpInstance ) +
            SEMI ).setName("udpInstantiation")

        parameterValueAssignment = Group( Literal("#") + LPAR + Group( delimitedList( expr ) ) + RPAR )
        namedPortConnection = Group( DOT + identifier + LPAR + expr + RPAR ).setName("namedPortConnection")#.setDebug()
        assert(r'.\abc (abc )' == namedPortConnection)
        modulePortConnection = expr | empty
        #~ moduleInstance = Group( Group ( identifier + Optional(range) ) +
            #~ ( delimitedList( modulePortConnection ) |
              #~ delimitedList( namedPortConnection ) ) )
        inst_args = Group( LPAR + (delimitedList( namedPortConnection ) |
                    delimitedList( modulePortConnection )) + RPAR).setName("inst_args")
        moduleInstance = Group( Group ( identifier + Optional(range) ) + inst_args ).setName("moduleInstance")#.setDebug()

        moduleInstantiation = Group( identifier +
            Optional( parameterValueAssignment ) +
            delimitedList( moduleInstance ).setName("moduleInstanceList") +
            SEMI ).setName("moduleInstantiation")

        parameterOverride = Group( "defparam" + delimitedList( paramAssgnmt ) + SEMI )
        task = Group( "task" + identifier + SEMI +
            ZeroOrMore( tfDecl ) +
            stmtOrNull +
            "endtask" )

        specparamDecl = Group( "specparam" + delimitedList( paramAssgnmt ) + SEMI )

        pathDescr1 = Group( LPAR + subscrIdentifier + "=>" + subscrIdentifier + RPAR )
        pathDescr2 = Group( LPAR + Group( delimitedList( subscrIdentifier ) ) + "*>" +
                                  Group( delimitedList( subscrIdentifier ) ) + RPAR )
        pathDescr3 = Group( LPAR + Group( delimitedList( subscrIdentifier ) ) + "=>" +
                                  Group( delimitedList( subscrIdentifier ) ) + RPAR )
        pathDelayValue = Group( ( LPAR + Group( delimitedList( mintypmaxExpr | expr ) ) + RPAR ) |
                                 mintypmaxExpr |
                                 expr )
        pathDecl = Group( ( pathDescr1 | pathDescr2 | pathDescr3 ) + EQ + pathDelayValue + SEMI ).setName("pathDecl")

        portConditionExpr = Forward()
        portConditionTerm = Optional(unop) + subscrIdentifier
        portConditionExpr << portConditionTerm + Optional( binop + portConditionExpr )
        polarityOp = oneOf("+ -")
        levelSensitivePathDecl1 = Group(
            if_ + Group(LPAR + portConditionExpr + RPAR) +
            subscrIdentifier + Optional( polarityOp ) + "=>" + subscrIdentifier + EQ +
            pathDelayValue +
            SEMI )
        levelSensitivePathDecl2 = Group(
            if_ + Group(LPAR + portConditionExpr + RPAR) +
            LPAR + Group( delimitedList( subscrIdentifier ) ) + Optional( polarityOp ) + "*>" +
                Group( delimitedList( subscrIdentifier ) ) + RPAR + EQ +
            pathDelayValue +
            SEMI )
        levelSensitivePathDecl = levelSensitivePathDecl1 | levelSensitivePathDecl2

        edgeIdentifier = posedge | negedge
        edgeSensitivePathDecl1 = Group(
            Optional( if_ + Group(LPAR + expr + RPAR) ) +
            LPAR + Optional( edgeIdentifier ) +
            subscrIdentifier + "=>" +
            LPAR + subscrIdentifier + Optional( polarityOp ) + COLON + expr + RPAR + RPAR +
            EQ +
            pathDelayValue +
            SEMI )
        edgeSensitivePathDecl2 = Group(
            Optional( if_ + Group(LPAR + expr + RPAR) ) +
            LPAR + Optional( edgeIdentifier ) +
            subscrIdentifier + "*>" +
            LPAR + delimitedList( subscrIdentifier ) + Optional( polarityOp ) + COLON + expr + RPAR + RPAR +
            EQ +
            pathDelayValue +
            SEMI )
        edgeSensitivePathDecl = edgeSensitivePathDecl1 | edgeSensitivePathDecl2

        edgeDescr = oneOf("01 10 0x x1 1x x0").setName("edgeDescr")

        timCheckEventControl = Group( posedge | negedge | (edge + LBRACK + delimitedList( edgeDescr ) + RBRACK ))
        timCheckCond = Forward()
        timCondBinop = oneOf("== === != !==")
        timCheckCondTerm = ( expr + timCondBinop + scalarConst ) | ( Optional("~") + expr )
        timCheckCond << ( ( LPAR + timCheckCond + RPAR ) | timCheckCondTerm )
        timCheckEvent = Group( Optional( timCheckEventControl ) +
                                subscrIdentifier +
                                Optional( "&&&" + timCheckCond ) )
        timCheckLimit = expr
        controlledTimingCheckEvent = Group( timCheckEventControl + subscrIdentifier +
                                            Optional( "&&&" + timCheckCond ) )
        notifyRegister = identifier

        systemTimingCheck1 = Group( "$setup" +
            LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit +
            Optional( COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck2 = Group( "$hold" +
            LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit +
            Optional( COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck3 = Group( "$period" +
            LPAR + controlledTimingCheckEvent + COMMA + timCheckLimit +
            Optional( COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck4 = Group( "$width" +
            LPAR + controlledTimingCheckEvent + COMMA + timCheckLimit +
            Optional( COMMA + expr + COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck5 = Group( "$skew" +
            LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit +
            Optional( COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck6 = Group( "$recovery" +
            LPAR + controlledTimingCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit +
            Optional( COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck7 = Group( "$setuphold" +
            LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit + COMMA + timCheckLimit +
            Optional( COMMA + notifyRegister ) + RPAR +
            SEMI )
        systemTimingCheck = (FollowedBy('$') + ( systemTimingCheck1 | systemTimingCheck2 | systemTimingCheck3 |
            systemTimingCheck4 | systemTimingCheck5 | systemTimingCheck6 | systemTimingCheck7 )).setName("systemTimingCheck")
        sdpd = if_ + Group(LPAR + expr + RPAR) + \
            ( pathDescr1 | pathDescr2 ) + EQ + pathDelayValue + SEMI

        specifyItem = ~Keyword("endspecify") +(
            specparamDecl |
            pathDecl |
            levelSensitivePathDecl |
            edgeSensitivePathDecl |
            systemTimingCheck |
            sdpd
            )
        """
        x::= <specparam_declaration>
        x||= <path_declaration>
        x||= <level_sensitive_path_declaration>
        x||= <edge_sensitive_path_declaration>
        x||= <system_timing_check>
        x||= <sdpd>
        """
        specifyBlock = Group( "specify" + ZeroOrMore( specifyItem ) + "endspecify" ).setName("specifyBlock")

        moduleItem = ~Keyword("endmodule") + (
            parameterDecl |
            inputDecl |
            outputDecl |
            inoutDecl |
            regDecl |
            netDecl3 |
            netDecl1 |
            netDecl2 |
            timeDecl |
            integerDecl |
            realDecl |
            eventDecl |
            gateDecl |
            parameterOverride |
            continuousAssign |
            specifyBlock |
            initialStmt |
            alwaysStmt |
            task |
            functionDecl |
            # these have to be at the end - they start with identifiers
            moduleInstantiation |
            udpInstantiation
            )
        """  All possible moduleItems, from Verilog grammar spec
        x::= <parameter_declaration>
        x||= <input_declaration>
        x||= <output_declaration>
        x||= <inout_declaration>
        ?||= <net_declaration>  (spec does not seem consistent for this item)
        x||= <reg_declaration>
        x||= <time_declaration>
        x||= <integer_declaration>
        x||= <real_declaration>
        x||= <event_declaration>
        x||= <gate_declaration>
        x||= <UDP_instantiation>
        x||= <module_instantiation>
        x||= <parameter_override>
        x||= <continuous_assign>
        x||= <specify_block>
        x||= <initial_statement>
        x||= <always_statement>
        x||= <task>
        x||= <function>
        """
        portRef = subscrIdentifier
        portExpr = portRef | Group( LBRACE + delimitedList( portRef ) + RBRACE )
        port = portExpr | Group( ( DOT + identifier + LPAR + portExpr + RPAR ) )

        moduleHdr = Group ( oneOf("module macromodule") + identifier +
                 Optional( LPAR + Group( Optional( delimitedList(
                                    Group(oneOf("input output") +
                                            (netDecl1Arg | netDecl2Arg | netDecl3Arg) ) |
                                    port ) ) ) +
                            RPAR ) + SEMI ).setName("moduleHdr")

        module = Group(  moduleHdr +
                 Group( ZeroOrMore( moduleItem ) ) +
                 "endmodule" ).setName("module")#.setDebug()

        udpDecl = outputDecl | inputDecl | regDecl
        #~ udpInitVal = oneOf("1'b0 1'b1 1'bx 1'bX 1'B0 1'B1 1'Bx 1'BX 1 0 x X")
        udpInitVal = (Regex("1'[bB][01xX]") | Regex("[01xX]")).setName("udpInitVal")
        udpInitialStmt = Group( "initial" +
            identifier + EQ + udpInitVal + SEMI ).setName("udpInitialStmt")

        levelSymbol = oneOf("0   1   x   X   ?   b   B")
        levelInputList = Group( OneOrMore( levelSymbol ).setName("levelInpList") )
        outputSymbol = oneOf("0   1   x   X")
        combEntry = Group( levelInputList + COLON + outputSymbol + SEMI )
        edgeSymbol = oneOf("r   R   f   F   p   P   n   N   *")
        edge = Group( LPAR + levelSymbol + levelSymbol + RPAR ) | \
               Group( edgeSymbol )
        edgeInputList = Group( ZeroOrMore( levelSymbol ) + edge + ZeroOrMore( levelSymbol ) )
        inputList = levelInputList | edgeInputList
        seqEntry = Group( inputList + COLON + levelSymbol + COLON + ( outputSymbol | "-" ) + SEMI ).setName("seqEntry")
        udpTableDefn = Group( "table" +
            OneOrMore( combEntry | seqEntry ) +
            "endtable" ).setName("table")

        """
        <UDP>
        ::= primitive <name_of_UDP> ( <name_of_variable> <,<name_of_variable>>* ) ;
                <UDP_declaration>+
                <UDP_initial_statement>?
                <table_definition>
                endprimitive
        """
        udp = Group( "primitive" + identifier +
            LPAR + Group( delimitedList( identifier ) ) + RPAR + SEMI +
            OneOrMore( udpDecl ) +
            Optional( udpInitialStmt ) +
            udpTableDefn +
            "endprimitive" )

        verilogbnf = OneOrMore( module | udp ) + StringEnd()

        verilogbnf.ignore( cppStyleComment )
        verilogbnf.ignore( compilerDirective )

    return verilogbnf


def test( strng ):
    tokens = []
    try:
        tokens = Verilog_BNF().parseString( strng )
    except ParseException as err:
        print(err.line)
        print(" "*(err.column-1) + "^")
        print(err)
    return tokens


#~ if __name__ == "__main__":
if 0:
    import pprint
    toptest = """
        module TOP( in, out );
        input [7:0] in;
        output [5:0] out;
        COUNT_BITS8 count_bits( .IN( in ), .C( out ) );
        endmodule"""
    pprint.pprint( test(toptest).asList() )

else:
    def main():
        print("Verilog parser test (V %s)" % __version__)
        print(" - using pyparsing version", pyparsing.__version__)
        print(" - using Python version", sys.version)
        if packratOn: print(" - using packrat parsing")
        print()

        import os
        import gc

        failCount = 0
        Verilog_BNF()
        numlines = 0
        startTime = time.clock()
        fileDir = "verilog"
        #~ fileDir = "verilog/new"
        #~ fileDir = "verilog/new2"
        #~ fileDir = "verilog/new3"
        allFiles = [f for f in os.listdir(fileDir) if f.endswith(".v")]
        #~ allFiles = [ "list_path_delays_test.v" ]
        #~ allFiles = [ "escapedIdent.v" ]
        #~ allFiles = filter( lambda f : f.startswith("a") and f.endswith(".v"), os.listdir(fileDir) )
        #~ allFiles = filter( lambda f : f.startswith("c") and f.endswith(".v"), os.listdir(fileDir) )
        #~ allFiles = [ "ff.v" ]

        pp = pprint.PrettyPrinter( indent=2 )
        totalTime = 0
        for vfile in allFiles:
            gc.collect()
            fnam = fileDir + "/"+vfile
            infile = open(fnam)
            filelines = infile.readlines()
            infile.close()
            print(fnam, len(filelines), end=' ')
            numlines += len(filelines)
            teststr = "".join(filelines)
            time1 = time.clock()
            tokens = test( teststr )
            time2 = time.clock()
            elapsed = time2-time1
            totalTime += elapsed
            if ( len( tokens ) ):
                print("OK", elapsed)
                #~ print "tokens="
                #~ pp.pprint( tokens.asList() )
                #~ print

                ofnam = fileDir + "/parseOutput/" + vfile + ".parsed.txt"
                outfile = open(ofnam,"w")
                outfile.write( teststr )
                outfile.write("\n")
                outfile.write("\n")
                outfile.write(pp.pformat(tokens.asList()))
                outfile.write("\n")
                outfile.close()
            else:
                print("failed", elapsed)
                failCount += 1
                for i,line in enumerate(filelines,1):
                    print("%4d: %s" % (i,line.rstrip()))
        endTime = time.clock()
        print("Total parse time:", totalTime)
        print("Total source lines:", numlines)
        print("Average lines/sec:", ( "%.1f" % (float(numlines)/(totalTime+.05 ) ) ))
        if failCount:
            print("FAIL - %d files failed to parse" % failCount)
        else:
            print("SUCCESS - all files parsed")

        return 0

    #~ from line_profiler import LineProfiler
    #~ from pyparsing import ParseResults
    #~ lp = LineProfiler(ParseResults.__init__)

    main()

    #~ lp.print_stats()
    #~ import hotshot
    #~ p = hotshot.Profile("vparse.prof",1,1)
    #~ p.start()
    #~ main()
    #~ p.stop()
    #~ p.close()
