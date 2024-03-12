#
# decaf_parser.py
#
# Rudimentary parser for decaf language, used in Stanford University CS143
# (https://web.stanford.edu/class/archive/cs/cs143/cs143.1128/handouts/030%20Decaf%20Specification.pdf)
#
# To convert this parser into one that gives more of an AST, change all the Group wrappers to add parse
# actions that will result in ASTNode classes, or statement-specific subclasses.
#
# Copyright 2018, Paul McGuire
#
"""
    Program ::= Decl+
    Decl ::= VariableDecl | FunctionDecl  | ClassDecl | InterfaceDecl
    VariableDecl ::= Variable ; 
    Variable ::= Type ident 
    Type ::= int | double | bool | string | ident | Type [] 
    FunctionDecl ::= Type ident ( Formals ) StmtBlock | void ident ( Formals ) StmtBlock 
    Formals ::= Variable+, |  e 
    ClassDecl ::= class ident <extends ident>  <implements ident + ,>  { Field* } 
    Field ::= VariableDecl | FunctionDecl 
    InterfaceDecl ::= interface ident { Prototype* } 
    Prototype ::= Type ident ( Formals ) ; | void ident ( Formals ) ; 
    StmtBlock ::= { VariableDecl*  Stmt* } 
    Stmt ::=  <Expr> ; | IfStmt  | WhileStmt |  ForStmt | BreakStmt   | ReturnStmt  | PrintStmt  | StmtBlock 
    IfStmt ::= if ( Expr ) Stmt <else Stmt> 
    WhileStmt ::= while ( Expr ) Stmt 
    ForStmt ::= for ( <Expr> ; Expr ; <Expr> ) Stmt 
    ReturnStmt ::= return <Expr> ; 
    BreakStmt ::= break ; 
    PrintStmt ::= Print ( Expr+, ) ; 
    Expr ::= LValue = Expr | Constant | LValue | this | Call
            | ( Expr ) 
            | Expr + Expr | Expr - Expr | Expr * Expr | Expr / Expr |  Expr % Expr | - Expr 
            | Expr < Expr | Expr <= Expr | Expr > Expr | Expr >= Expr | Expr == Expr | Expr != Expr 
            | Expr && Expr | Expr || Expr | ! Expr 
            | ReadInteger ( ) | ReadLine ( ) | new ident | NewArray ( Expr , Typev) 
    LValue ::= ident |  Expr  . ident | Expr [ Expr ] 
    Call ::= ident  ( Actuals ) |  Expr  .  ident  ( Actuals ) 
    Actuals ::=  Expr+, | e 
    Constant ::= intConstant | doubleConstant | boolConstant |  stringConstant | null
"""
import pyparsing as pp
from pyparsing import pyparsing_common as ppc
pp.ParserElement.enablePackrat()

# keywords
keywords = (VOID, INT, DOUBLE, BOOL, STRING, CLASS, INTERFACE, NULL, THIS, EXTENDS, IMPLEMENTS, FOR, WHILE,
            IF, ELSE, RETURN, BREAK, NEW, NEWARRAY, PRINT, READINTEGER, READLINE, TRUE, FALSE) = map(pp.Keyword,
            """void int double bool string class interface null this extends implements or while
               if else return break new NewArray Print ReadInteger ReadLine true false""".split())
keywords = pp.MatchFirst(list(keywords))

LPAR, RPAR, LBRACE, RBRACE, LBRACK, RBRACK, DOT, EQ, COMMA, SEMI = map(pp.Suppress, "(){}[].=,;")
hexConstant = pp.Regex(r"0[xX][0-9a-fA-F]+").addParseAction(lambda t: int(t[0][2:], 16))
intConstant = hexConstant | ppc.integer
doubleConstant = ppc.real
boolConstant = TRUE | FALSE
stringConstant = pp.dblQuotedString
null = NULL
constant = doubleConstant | boolConstant | intConstant | stringConstant | null
ident = ~keywords + pp.Word(pp.alphas, pp.alphanums+'_')
type_ = pp.Group((INT | DOUBLE | BOOL | STRING | ident) + pp.ZeroOrMore("[]"))

variable = type_ + ident
variable_decl = variable + SEMI

expr = pp.Forward()
expr_parens = pp.Group(LPAR + expr + RPAR)
actuals = pp.Optional(pp.delimitedList(expr))
call = pp.Group(ident("call_ident") + LPAR + actuals("call_args") + RPAR
                | (expr_parens + pp.ZeroOrMore(DOT + ident))("call_ident_expr") + LPAR + actuals("call_args") + RPAR)
lvalue = ((ident | expr_parens) 
           + pp.ZeroOrMore(DOT + (ident | expr_parens)) 
           + pp.ZeroOrMore(LBRACK + expr + RBRACK))
assignment = pp.Group(lvalue("lhs") + EQ + expr("rhs"))
read_integer = pp.Group(READINTEGER + LPAR + RPAR)
read_line = pp.Group(READLINE + LPAR + RPAR)
new_statement = pp.Group(NEW + ident)
new_array = pp.Group(NEWARRAY + LPAR + expr + COMMA + type_ + RPAR)
rvalue = constant | call | read_integer | read_line | new_statement | new_array | ident
arith_expr = pp.infixNotation(rvalue,
    [
    ('-', 1, pp.opAssoc.RIGHT,),
    (pp.oneOf("* / %"), 2, pp.opAssoc.LEFT,),
    (pp.oneOf("+ -"), 2, pp.opAssoc.LEFT,),
    ])
comparison_expr = pp.infixNotation(arith_expr, 
    [
    ('!', 1, pp.opAssoc.RIGHT,),
    (pp.oneOf("< > <= >="), 2, pp.opAssoc.LEFT,),
    (pp.oneOf("== !="), 2, pp.opAssoc.LEFT,),
    (pp.oneOf("&&"), 2, pp.opAssoc.LEFT,),
    (pp.oneOf("||"), 2, pp.opAssoc.LEFT,),
    ])
expr <<= (assignment
          | call
          | THIS
          | comparison_expr
          | arith_expr
          | lvalue
          | constant
          | read_integer
          | read_line
          | new_statement
          | new_array
          )

stmt = pp.Forward()
print_stmt = pp.Group(PRINT("statement") + LPAR + pp.Group(pp.Optional(pp.delimitedList(expr)))("args") + RPAR + SEMI)
break_stmt = pp.Group(BREAK("statement") + SEMI)
return_stmt = pp.Group(RETURN("statement") + expr + SEMI)
for_stmt = pp.Group(FOR("statement") + LPAR + pp.Optional(expr) + SEMI + expr + SEMI + pp.Optional(expr) + RPAR + stmt)
while_stmt = pp.Group(WHILE("statement") + LPAR + expr + RPAR + stmt)
if_stmt = pp.Group(IF("statement")
                   + LPAR + pp.Group(expr)("condition") + RPAR
                   + pp.Group(stmt)("then_statement")
                   + pp.Group(pp.Optional(ELSE + stmt))("else_statement"))
stmt_block = pp.Group(LBRACE + pp.ZeroOrMore(variable_decl) + pp.ZeroOrMore(stmt) + RBRACE)
stmt <<= (if_stmt
          | while_stmt
          | for_stmt
          | break_stmt
          | return_stmt
          | print_stmt
          | stmt_block
          | pp.Group(expr + SEMI)
          )

formals = pp.Optional(pp.delimitedList(variable))
prototype = pp.Group((type_ | VOID)("return_type")
                     + ident("function_name")
                     + LPAR + formals("args") + RPAR + SEMI)("prototype")
function_decl = pp.Group((type_ | VOID)("return_type") + ident("function_name")
                         + LPAR + formals("args") + RPAR
                         + stmt_block("body"))("function_decl")

interface_decl = pp.Group(INTERFACE + ident("interface_name")
                          + LBRACE + pp.ZeroOrMore(prototype)("prototypes") + RBRACE)("interface")
field = variable_decl | function_decl
class_decl = pp.Group(CLASS + ident("class_name")
              + pp.Optional(EXTENDS + ident)("extends")
              + pp.Optional(IMPLEMENTS + pp.delimitedList(ident))("implements")
              + LBRACE + pp.ZeroOrMore(field)("fields") + RBRACE)("class_decl")

decl = variable_decl | function_decl | class_decl | interface_decl | prototype
program = pp.OneOrMore(pp.Group(decl))
decaf_parser = program

stmt.runTests("""\
    sin(30);
    a = 1;
    b = 1 + 1;
    b = 1 != 2 && false;
    print("A");
    a.b = 100;
    a.b = 100.0;
    a[100] = b;
    a[0][0] = 2;
    a = 0x1234;
""")

test_program = """
    void getenv(string var);
    int main(string[] args) {
        if (a > 100) {
            Print(a, " is too big");
        } else if (a < 100) {
            Print(a, " is too small");
        } else {
            Print(a, "just right!");
        }
    }
"""

print(decaf_parser.parseString(test_program).dump())
