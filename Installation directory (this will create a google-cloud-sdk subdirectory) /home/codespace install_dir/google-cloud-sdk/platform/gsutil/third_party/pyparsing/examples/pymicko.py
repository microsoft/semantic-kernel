#!/usr/bin/python

#    Python/pyparsing educational microC compiler v1.0
#    Copyright (C) 2009  Zarko Zivanov
#    (largely based on flex/bison microC compiler by Zorica Suvajdzin, used with her permission;
#     current version can be found at http://www.acs.uns.ac.rs, under "Programski Prevodioci" [Serbian site])
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of the GNU General Public License can be found at <https://www.gnu.org/licenses/>.

from pyparsing import *
from sys import stdin, argv, exit

#defines debug level
# 0 - no debug
# 1 - print parsing results
# 2 - print parsing results and symbol table
# 3 - print parsing results only, without executing parse actions (grammar-only testing)
DEBUG = 0

##########################################################################################
##########################################################################################

#                               About microC language and microC compiler

# microC language and microC compiler are educational tools, and their goal is to show some basic principles
# of writing a C language compiler. Compiler represents one (relatively simple) solution, not necessarily the best one.
# This Python/pyparsing version is made using Python 2.6.4 and pyparsing 1.5.2 (and it may contain errors :) )

##########################################################################################
##########################################################################################

#                               Model of the used hypothetical processor

# The reason behind using a hypothetical processor is to simplify code generation and to concentrate on the compiler itself.
# This compiler can relatively easily be ported to x86, but one must know all the little details about which register
# can be used for what, which registers are default for various operations, etc.

# The hypothetical processor has 16 registers, called %0 to %15. Register %13 is used for the function return value (x86's eax),
# %14 is the stack frame pointer (x86's ebp) and %15 is the stack pointer (x86's esp). All data-handling instructions can be
# unsigned (suffix U), or signed (suffix S). These are ADD, SUB, MUL and DIV. These are three-address instructions,
# the first two operands are input, the third one is output. Whether these operands are registers, memory or constant
# is not relevant, all combinations are possible (except that output cannot be a constant). Constants are writen with a $ prefix (10-base only).
# Conditional jumps are handled by JXXY instructions, where XX is LT, GT, LE, GE, EQ, NE (less than, greater than, less than or equal, etc.)
# and Y is U or S (unsigned or signed, except for JEQ i JNE). Unconditional jump is JMP. The move instruction is MOV.
# Function handling is done using CALL, RET, PUSH and POP (C style function calls). Static data is defined using the WORD directive
# (example: variable: WORD 1), whose only argument defines the number of locations that are reserved.

##########################################################################################
##########################################################################################

#                               Grammar of The microC Programming Language
# (small subset of C made for compiler course at Faculty of Technical Sciences, Chair for Applied Computer Sciences, Novi Sad, Serbia)

# Patterns:

# letter
#  ->    "_" | "a" | "A" | "b" | "B" | "c" | "C" | "d" | "D" | "e" | "E" | "f"
#      | "F" | "g" | "G" | "h" | "H" | "i" | "I" | "j" | "J" | "k" | "K" | "l"
#      | "L" | "m" | "M" | "n" | "N" | "o" | "O" | "p" | "P" | "q" | "Q" | "r"
#      | "R" | "s" | "S" | "t" | "T" | "u" | "U" | "v" | "V" | "w" | "W" | "x"
#      | "X" | "y" | "Y" | "z" | "Z"

# digit
#  ->  "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

# identifier
#  ->  letter ( letter | digit )*

# int_constant
#  ->  digit +

# unsigned_constant
#  ->  digit + ( "u" | "U" )

# Productions:

# program
#  ->  variable_list function_list
#  ->  function_list

# variable_list
#  ->  variable ";"
#  ->  variable_list variable ";"

# variable
#  ->  type identifier

# type
#  ->  "int"
#  ->  "unsigned"

# function_list
#  ->  function
#  ->  function_list function

# function
#  ->  type identifier "(" parameters ")" body

# parameters
#  ->  <empty>
#  ->  parameter_list

# parameter_list
#  ->  variable
#  ->  parameter_list "," variable

# body
#  ->  "{" variable_list statement_list "}"
#  ->  "{" statement_list "}"

# statement_list
#  ->  <empty>
#  ->  statement_list statement

# statement
#  ->  assignement_statement
#  ->  function_call_statement
#  ->  if_statement
#  ->  while_statement
#  ->  return_statement
#  ->  compound_statement

# assignement_statement
#  ->  identifier "=" num_exp ";"

# num_exp
#  ->  mul_exp
#  ->  num_exp "+" mul_exp
#  ->  num_exp "-" mul_exp

# mul_exp
#  ->  exp
#  ->  mul_exp "*" exp
#  ->  mul_exp "/" exp

# exp
#  ->  constant
#  ->  identifier
#  ->  function_call
#  ->  "(" num_exp ")"
#  ->  "+" exp
#  ->  "-" exp

# constant
#  ->  int_constant
#  ->  unsigned_constant

# function_call
#  ->  identifier "(" arguments ")"

# arguments
#  ->  <empty>
#  ->  argument_list

# argument_list
#  ->  num_exp
#  ->  argument_list "," num_exp

# function_call_statement
#  ->  function_call ";"

# if_statement
#  ->  "if" "(" log_exp ")" statement
#  ->  "if" "(" log_exp ")" statement "else" statement
#  ->   ->   ->   ->   ->   ->   -> ->   2

# log_exp
#  ->  and_exp
#  ->  log_exp "||" and_exp

# and_exp
#  ->  rel_exp
#  ->  and_exp "&&" rel_exp

# rel_exp
#  ->  num_exp  "<" num_exp
#  ->  num_exp  ">" num_exp
#  ->  num_exp  "<=" num_exp
#  ->  num_exp  ">=" num_exp
#  ->  num_exp  "==" num_exp
#  ->  num_exp  "!=" num_exp

# while_statement
#  ->  "while" "(" log_exp ")" statement

# return_statement
#  ->  "return" num_exp ";"

# compound_statement
#  ->  "{" statement_list "}"

# Comment: /* a comment */

##########################################################################################
##########################################################################################

class Enumerate(dict):
    """C enum emulation (original by Scott David Daniels)"""
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            self[number] = name

class SharedData(object):
    """Data used in all three main classes"""

    #Possible kinds of symbol table entries
    KINDS = Enumerate("NO_KIND WORKING_REGISTER GLOBAL_VAR FUNCTION PARAMETER LOCAL_VAR CONSTANT")
    #Supported types of functions and variables
    TYPES = Enumerate("NO_TYPE INT UNSIGNED")

    #bit size of variables
    TYPE_BIT_SIZE = 16
    #min/max values of constants
    MIN_INT = -2 ** (TYPE_BIT_SIZE - 1)
    MAX_INT = 2 ** (TYPE_BIT_SIZE - 1) - 1
    MAX_UNSIGNED = 2 ** TYPE_BIT_SIZE - 1
    #available working registers (the last one is the register for function's return value!)
    REGISTERS = "%0 %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 %11 %12 %13".split()
    #register for function's return value
    FUNCTION_REGISTER = len(REGISTERS) - 1
    #the index of last working register
    LAST_WORKING_REGISTER = len(REGISTERS) - 2
    #list of relational operators
    RELATIONAL_OPERATORS = "< > <= >= == !=".split()

    def __init__(self):
        #index of the currently parsed function
        self.functon_index = 0
        #name of the currently parsed function
        self.functon_name = 0
        #number of parameters of the currently parsed function
        self.function_params = 0
        #number of local variables of the currently parsed function
        self.function_vars = 0

##########################################################################################
##########################################################################################

class ExceptionSharedData(object):
    """Class for exception handling data"""

    def __init__(self):
        #position in currently parsed text
        self.location = 0
        #currently parsed text
        self.text = ""

    def setpos(self, location, text):
        """Helper function for setting curently parsed text and position"""
        self.location = location
        self.text = text

exshared = ExceptionSharedData()

class SemanticException(Exception):
    """Exception for semantic errors found during parsing, similar to ParseException.
       Introduced because ParseException is used internally in pyparsing and custom
       messages got lost and replaced by pyparsing's generic errors.
    """

    def __init__(self, message, print_location=True):
        super(SemanticException,self).__init__()
        self._message = message
        self.location = exshared.location
        self.print_location = print_location
        if exshared.location != None:
            self.line = lineno(exshared.location, exshared.text)
            self.col = col(exshared.location, exshared.text)
            self.text = line(exshared.location, exshared.text)
        else:
            self.line = self.col = self.text = None

    def _get_message(self):
        return self._message
    def _set_message(self, message):
        self._message = message
    message = property(_get_message, _set_message)

    def __str__(self):
        """String representation of the semantic error"""
        msg = "Error"
        if self.print_location and (self.line != None):
            msg += " at line %d, col %d" % (self.line, self.col)
        msg += ": %s" % self.message
        if self.print_location and (self.line != None):
            msg += "\n%s" % self.text
        return msg

##########################################################################################
##########################################################################################

class SymbolTableEntry(object):
    """Class which represents one symbol table entry."""

    def __init__(self, sname = "", skind = 0, stype = 0, sattr = None, sattr_name = "None"):
        """Initialization of symbol table entry.
           sname - symbol name
           skind - symbol kind
           stype - symbol type
           sattr - symbol attribute
           sattr_name - symbol attribute name (used only for table display)
        """
        self.name = sname
        self.kind = skind
        self.type = stype
        self.attribute = sattr
        self.attribute_name = sattr_name
        self.param_types = []

    def set_attribute(self, name, value):
        """Sets attribute's name and value"""
        self.attribute_name = name
        self.attribute = value

    def attribute_str(self):
        """Returns attribute string (used only for table display)"""
        return "{0}={1}".format(self.attribute_name, self.attribute) if self.attribute != None else "None"

class SymbolTable(object):
    """Class for symbol table of microC program"""

    def __init__(self, shared):
        """Initialization of the symbol table"""
        self.table = []
        self.lable_len = 0
        #put working registers in the symbol table
        for reg in range(SharedData.FUNCTION_REGISTER+1):
            self.insert_symbol(SharedData.REGISTERS[reg], SharedData.KINDS.WORKING_REGISTER, SharedData.TYPES.NO_TYPE)
        #shared data
        self.shared = shared

    def error(self, text=""):
        """Symbol table error exception. It should happen only if index is out of range while accessing symbol table.
           This exeption is not handled by the compiler, so as to allow traceback printing
        """
        if text == "":
            raise Exception("Symbol table index out of range")
        else:
            raise Exception("Symbol table error: %s" % text)

    def display(self):
        """Displays the symbol table content"""
        #Finding the maximum length for each column
        sym_name = "Symbol name"
        sym_len = max(max(len(i.name) for i in self.table),len(sym_name))
        kind_name = "Kind"
        kind_len = max(max(len(SharedData.KINDS[i.kind]) for i in self.table),len(kind_name))
        type_name = "Type"
        type_len = max(max(len(SharedData.TYPES[i.type]) for i in self.table),len(type_name))
        attr_name = "Attribute"
        attr_len = max(max(len(i.attribute_str()) for i in self.table),len(attr_name))
        #print table header
        print("{0:3s} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}} | {9:s}".format(" No", sym_name, sym_len, kind_name, kind_len, type_name, type_len, attr_name, attr_len, "Parameters"))
        print("-----------------------------" + "-" * (sym_len + kind_len + type_len + attr_len))
        #print symbol table
        for i,sym in enumerate(self.table):
            parameters = ""
            for p in sym.param_types:
                if parameters == "":
                    parameters = "{0}".format(SharedData.TYPES[p])
                else:
                    parameters += ", {0}".format(SharedData.TYPES[p])
            print("{0:3d} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}} | ({9})".format(i, sym.name, sym_len, SharedData.KINDS[sym.kind], kind_len, SharedData.TYPES[sym.type], type_len, sym.attribute_str(), attr_len, parameters))

    def insert_symbol(self, sname, skind, stype):
        """Inserts new symbol at the end of the symbol table.
           Returns symbol index
           sname - symbol name
           skind - symbol kind
           stype - symbol type
        """
        self.table.append(SymbolTableEntry(sname, skind, stype))
        self.table_len = len(self.table)
        return self.table_len-1

    def clear_symbols(self, index):
        """Clears all symbols begining with the index to the end of table"""
        try:
            del self.table[index:]
        except Exception:
            self.error()
        self.table_len = len(self.table)

    def lookup_symbol(self, sname, skind=list(SharedData.KINDS.keys()), stype=list(SharedData.TYPES.keys())):
        """Searches for symbol, from the end to the begining.
           Returns symbol index or None
           sname - symbol name
           skind - symbol kind (one kind, list of kinds, or None) deafult: any kind
           stype - symbol type (or None) default: any type
        """
        skind = skind if isinstance(skind, list) else [skind]
        stype = stype if isinstance(stype, list) else [stype]
        for i, sym in [[x, self.table[x]] for x in range(len(self.table) - 1, SharedData.LAST_WORKING_REGISTER, -1)]:
            if (sym.name == sname) and (sym.kind in skind) and (sym.type in stype):
                return i
        return None

    def insert_id(self, sname, skind, skinds, stype):
        """Inserts a new identifier at the end of the symbol table, if possible.
           Returns symbol index, or raises an exception if the symbol alredy exists
           sname   - symbol name
           skind   - symbol kind
           skinds  - symbol kinds to check for
           stype   - symbol type
        """
        index = self.lookup_symbol(sname, skinds)
        if index == None:
            index = self.insert_symbol(sname, skind, stype)
            return index
        else:
            raise SemanticException("Redefinition of '%s'" % sname)

    def insert_global_var(self, vname, vtype):
        "Inserts a new global variable"
        return self.insert_id(vname, SharedData.KINDS.GLOBAL_VAR, [SharedData.KINDS.GLOBAL_VAR, SharedData.KINDS.FUNCTION], vtype)

    def insert_local_var(self, vname, vtype, position):
        "Inserts a new local variable"
        index = self.insert_id(vname, SharedData.KINDS.LOCAL_VAR, [SharedData.KINDS.LOCAL_VAR, SharedData.KINDS.PARAMETER], vtype)
        self.table[index].attribute = position

    def insert_parameter(self, pname, ptype):
        "Inserts a new parameter"
        index = self.insert_id(pname, SharedData.KINDS.PARAMETER, SharedData.KINDS.PARAMETER, ptype)
        #set parameter's attribute to it's ordinal number
        self.table[index].set_attribute("Index", self.shared.function_params)
        #set parameter's type in param_types list of a function
        self.table[self.shared.function_index].param_types.append(ptype)
        return index

    def insert_function(self, fname, ftype):
        "Inserts a new function"
        index = self.insert_id(fname, SharedData.KINDS.FUNCTION, [SharedData.KINDS.GLOBAL_VAR, SharedData.KINDS.FUNCTION], ftype)
        self.table[index].set_attribute("Params",0)
        return index

    def insert_constant(self, cname, ctype):
        """Inserts a constant (or returns index if the constant already exists)
           Additionally, checks for range.
        """
        index = self.lookup_symbol(cname, stype=ctype)
        if index == None:
            num = int(cname)
            if ctype == SharedData.TYPES.INT:
                if (num < SharedData.MIN_INT) or (num > SharedData.MAX_INT):
                    raise SemanticException("Integer constant '%s' out of range" % cname)
            elif ctype == SharedData.TYPES.UNSIGNED:
                if (num < 0) or (num > SharedData.MAX_UNSIGNED):
                    raise SemanticException("Unsigned constant '%s' out of range" % cname)
            index = self.insert_symbol(cname, SharedData.KINDS.CONSTANT, ctype)
        return index

    def same_types(self, index1, index2):
        """Returns True if both symbol table elements are of the same type"""
        try:
            same = self.table[index1].type == self.table[index2].type != SharedData.TYPES.NO_TYPE
        except Exception:
            self.error()
        return same

    def same_type_as_argument(self, index, function_index, argument_number):
        """Returns True if index and function's argument are of the same type
           index - index in symbol table
           function_index - function's index in symbol table
           argument_number - # of function's argument
        """
        try:
            same = self.table[function_index].param_types[argument_number] == self.table[index].type
        except Exception:
            self.error()
        return same

    def get_attribute(self, index):
        try:
            return self.table[index].attribute
        except Exception:
            self.error()

    def set_attribute(self, index, value):
        try:
            self.table[index].attribute = value
        except Exception:
            self.error()

    def get_name(self, index):
        try:
            return self.table[index].name
        except Exception:
            self.error()

    def get_kind(self, index):
        try:
            return self.table[index].kind
        except Exception:
            self.error()

    def get_type(self, index):
        try:
            return self.table[index].type
        except Exception:
            self.error()

    def set_type(self, index, stype):
        try:
            self.table[index].type = stype
        except Exception:
            self.error()

##########################################################################################
##########################################################################################

class CodeGenerator(object):
    """Class for code generation methods."""

    #dictionary of relational operators
    RELATIONAL_DICT = {op:i for i, op in enumerate(SharedData.RELATIONAL_OPERATORS)}
    #conditional jumps for relational operators
    CONDITIONAL_JUMPS = ["JLTS", "JGTS", "JLES", "JGES", "JEQ ", "JNE ",
                         "JLTU", "JGTU", "JLEU", "JGEU", "JEQ ", "JNE "]
    #opposite conditional jumps for relational operators
    OPPOSITE_JUMPS = ["JGES", "JLES", "JGTS", "JLTS", "JNE ", "JEQ ",
                      "JGEU", "JLEU", "JGTU", "JLTU", "JNE ", "JEQ "]
    #supported operations
    OPERATIONS = {"+" : "ADD", "-" : "SUB", "*" : "MUL", "/" : "DIV"}
    #suffixes for signed and unsigned operations (if no type is specified, unsigned will be assumed)
    OPSIGNS = {SharedData.TYPES.NO_TYPE : "U", SharedData.TYPES.INT : "S", SharedData.TYPES.UNSIGNED : "U"}
    #text at start of data segment
    DATA_START_TEXT = "#DATA"
    #text at start of code segment
    CODE_START_TEXT = "#CODE"

    def __init__(self, shared, symtab):
        #generated code
        self.code = ""
        #prefix for internal labels
        self.internal = "@"
        #suffix for label definition
        self.definition = ":"
        #list of free working registers
        self.free_registers = list(range(SharedData.FUNCTION_REGISTER, -1, -1))
        #list of used working registers
        self.used_registers = []
        #list of used registers needed when function call is inside of a function call
        self.used_registers_stack = []
        #shared data
        self.shared = shared
        #symbol table
        self.symtab = symtab

    def error(self, text):
        """Compiler error exception. It should happen only if something is wrong with compiler.
           This exeption is not handled by the compiler, so as to allow traceback printing
        """
        raise Exception("Compiler error: %s" % text)

    def take_register(self, rtype = SharedData.TYPES.NO_TYPE):
        """Reserves one working register and sets its type"""
        if len(self.free_registers) == 0:
            self.error("no more free registers")
        reg = self.free_registers.pop()
        self.used_registers.append(reg)
        self.symtab.set_type(reg, rtype)
        return reg

    def take_function_register(self, rtype = SharedData.TYPES.NO_TYPE):
        """Reserves register for function return value and sets its type"""
        reg = SharedData.FUNCTION_REGISTER
        if reg not in self.free_registers:
            self.error("function register already taken")
        self.free_registers.remove(reg)
        self.used_registers.append(reg)
        self.symtab.set_type(reg, rtype)
        return reg

    def free_register(self, reg):
        """Releases working register"""
        if reg not in self.used_registers:
            self.error("register %s is not taken" % self.REGISTERS[reg])
        self.used_registers.remove(reg)
        self.free_registers.append(reg)
        self.free_registers.sort(reverse = True)

    def free_if_register(self, index):
        """If index is a working register, free it, otherwise just return (helper function)"""
        if (index < 0) or (index > SharedData.FUNCTION_REGISTER):
            return
        else:
            self.free_register(index)

    def label(self, name, internal=False, definition=False):
        """Generates label name (helper function)
           name - label name
           internal - boolean value, adds "@" prefix to label
           definition - boolean value, adds ":" suffix to label
        """
        return "{0}{1}{2}".format(self.internal if internal else "", name, self.definition if definition else "")

    def symbol(self, index):
        """Generates symbol name from index"""
        #if index is actually a string, just return it
        if isinstance(index, str):
            return index
        elif (index < 0) or (index >= self.symtab.table_len):
            self.error("symbol table index out of range")
        sym = self.symtab.table[index]
        #local variables are located at negative offset from frame pointer register
        if sym.kind == SharedData.KINDS.LOCAL_VAR:
            return "-{0}(1:%14)".format(sym.attribute * 4 + 4)
        #parameters are located at positive offset from frame pointer register
        elif sym.kind == SharedData.KINDS.PARAMETER:
            return "{0}(1:%14)".format(8 + sym.attribute * 4)
        elif sym.kind == SharedData.KINDS.CONSTANT:
            return "${0}".format(sym.name)
        else:
            return "{0}".format(sym.name)

    def save_used_registers(self):
        """Pushes all used working registers before function call"""
        used = self.used_registers[:]
        del self.used_registers[:]
        self.used_registers_stack.append(used[:])
        used.sort()
        for reg in used:
            self.newline_text("PUSH\t%s" % SharedData.REGISTERS[reg], True)
        self.free_registers.extend(used)
        self.free_registers.sort(reverse = True)

    def restore_used_registers(self):
        """Pops all used working registers after function call"""
        used = self.used_registers_stack.pop()
        self.used_registers = used[:]
        used.sort(reverse = True)
        for reg in used:
            self.newline_text("POP \t%s" % SharedData.REGISTERS[reg], True)
            self.free_registers.remove(reg)

    def text(self, text):
        """Inserts text into generated code"""
        self.code += text

    def prepare_data_segment(self):
        """Inserts text at the start of data segment"""
        self.text(self.DATA_START_TEXT)

    def prepare_code_segment(self):
        """Inserts text at the start of code segment"""
        self.newline_text(self.CODE_START_TEXT)

    def newline(self, indent=False):
        """Inserts a newline, optionally with indentation."""
        self.text("\n")
        if indent:
            self.text("\t\t\t")

    def newline_text(self, text, indent = False):
        """Inserts a newline and text, optionally with indentation (helper function)"""
        self.newline(indent)
        self.text(text)

    def newline_label(self, name, internal=False, definition=False):
        """Inserts a newline and a label (helper function)
           name - label name
           internal - boolean value, adds "@" prefix to label
           definition - boolean value, adds ":" suffix to label
        """
        self.newline_text(self.label("{0}{1}{2}".format("@" if internal else "", name, ":" if definition else "")))

    def global_var(self, name):
        """Inserts a new static (global) variable definition"""
        self.newline_label(name, False, True)
        self.newline_text("WORD\t1", True)

    def arithmetic_mnemonic(self, op_name, op_type):
        """Generates an arithmetic instruction mnemonic"""
        return self.OPERATIONS[op_name] + self.OPSIGNS[op_type]

    def arithmetic(self, operation, operand1, operand2, operand3 = None):
        """Generates an arithmetic instruction
           operation - one of supporetd operations
           operandX - index in symbol table or text representation of operand
           First two operands are input, third one is output
        """
        if isinstance(operand1, int):
            output_type = self.symtab.get_type(operand1)
            self.free_if_register(operand1)
        else:
            output_type = None
        if isinstance(operand2, int):
            output_type = self.symtab.get_type(operand2) if output_type == None else output_type
            self.free_if_register(operand2)
        else:
            output_type = SharedData.TYPES.NO_TYPE if output_type == None else output_type
        #if operand3 is not defined, reserve one free register for it
        output = self.take_register(output_type) if operand3 == None else operand3
        mnemonic = self.arithmetic_mnemonic(operation, output_type)
        self.newline_text("{0}\t{1},{2},{3}".format(mnemonic, self.symbol(operand1), self.symbol(operand2), self.symbol(output)), True)
        return output

    def relop_code(self, relop, operands_type):
        """Returns code for relational operator
           relop - relational operator
           operands_type - int or unsigned
        """
        code = self.RELATIONAL_DICT[relop]
        offset = 0 if operands_type == SharedData.TYPES.INT else len(SharedData.RELATIONAL_OPERATORS)
        return code + offset

    def jump(self, relcode, opposite, label):
        """Generates a jump instruction
           relcode  - relational operator code
           opposite - generate normal or opposite jump
           label    - jump label
        """
        jump = self.OPPOSITE_JUMPS[relcode] if opposite else self.CONDITIONAL_JUMPS[relcode]
        self.newline_text("{0}\t{1}".format(jump, label), True)

    def unconditional_jump(self, label):
        """Generates an unconditional jump instruction
           label    - jump label
        """
        self.newline_text("JMP \t{0}".format(label), True)

    def move(self,operand1, operand2):
        """Generates a move instruction
           If the output operand (opernad2) is a working register, sets it's type
           operandX - index in symbol table or text representation of operand
        """
        if isinstance(operand1, int):
            output_type = self.symtab.get_type(operand1)
            self.free_if_register(operand1)
        else:
            output_type = SharedData.TYPES.NO_TYPE
        self.newline_text("MOV \t{0},{1}".format(self.symbol(operand1), self.symbol(operand2)), True)
        if isinstance(operand2, int):
            if self.symtab.get_kind(operand2) == SharedData.KINDS.WORKING_REGISTER:
                self.symtab.set_type(operand2, output_type)

    def push(self, operand):
        """Generates a push operation"""
        self.newline_text("PUSH\t%s" % self.symbol(operand), True)

    def pop(self, operand):
        """Generates a pop instruction"""
        self.newline_text("POP \t%s" % self.symbol(operand), True)

    def compare(self, operand1, operand2):
        """Generates a compare instruction
           operandX - index in symbol table
        """
        typ = self.symtab.get_type(operand1)
        self.free_if_register(operand1)
        self.free_if_register(operand2)
        self.newline_text("CMP{0}\t{1},{2}".format(self.OPSIGNS[typ], self.symbol(operand1), self.symbol(operand2)), True)

    def function_begin(self):
        """Inserts function name label and function frame initialization"""
        self.newline_label(self.shared.function_name, False, True)
        self.push("%14")
        self.move("%15", "%14")

    def function_body(self):
        """Inserts a local variable initialization and body label"""
        if self.shared.function_vars > 0:
            const = self.symtab.insert_constant("0{}".format(self.shared.function_vars * 4), SharedData.TYPES.UNSIGNED)
            self.arithmetic("-", "%15", const, "%15")
        self.newline_label(self.shared.function_name + "_body", True, True)

    def function_end(self):
        """Inserts an exit label and function return instructions"""
        self.newline_label(self.shared.function_name + "_exit", True, True)
        self.move("%14", "%15")
        self.pop("%14")
        self.newline_text("RET", True)

    def function_call(self, function, arguments):
        """Generates code for a function call
           function - function index in symbol table
           arguments - list of arguments (indexes in symbol table)
        """
        #push each argument to stack
        for arg in arguments:
            self.push(self.symbol(arg))
            self.free_if_register(arg)
        self.newline_text("CALL\t"+self.symtab.get_name(function), True)
        args = self.symtab.get_attribute(function)
        #generates stack cleanup if function has arguments
        if args > 0:
            args_space = self.symtab.insert_constant("{0}".format(args * 4), SharedData.TYPES.UNSIGNED)
            self.arithmetic("+", "%15", args_space, "%15")

##########################################################################################
##########################################################################################

class MicroC(object):
    """Class for microC parser/compiler"""

    def __init__(self):
        #Definitions of terminal symbols for microC programming language
        self.tId = Word(alphas+"_",alphanums+"_")
        self.tInteger = Word(nums).setParseAction(lambda x : [x[0], SharedData.TYPES.INT])
        self.tUnsigned = Regex(r"[0-9]+[uU]").setParseAction(lambda x : [x[0][:-1], SharedData.TYPES.UNSIGNED])
        self.tConstant = (self.tUnsigned | self.tInteger).setParseAction(self.constant_action)
        self.tType = Keyword("int").setParseAction(lambda x : SharedData.TYPES.INT) | \
                     Keyword("unsigned").setParseAction(lambda x : SharedData.TYPES.UNSIGNED)
        self.tRelOp = oneOf(SharedData.RELATIONAL_OPERATORS)
        self.tMulOp = oneOf("* /")
        self.tAddOp = oneOf("+ -")

        #Definitions of rules for global variables
        self.rGlobalVariable = (self.tType("type") + self.tId("name") +
                                FollowedBy(";")).setParseAction(self.global_variable_action)
        self.rGlobalVariableList = ZeroOrMore(self.rGlobalVariable + Suppress(";"))

        #Definitions of rules for numeric expressions
        self.rExp = Forward()
        self.rMulExp = Forward()
        self.rNumExp = Forward()
        self.rArguments = delimitedList(self.rNumExp("exp").setParseAction(self.argument_action))
        self.rFunctionCall = ((self.tId("name") + FollowedBy("(")).setParseAction(self.function_call_prepare_action) +
                              Suppress("(") + Optional(self.rArguments)("args") + Suppress(")")).setParseAction(self.function_call_action)
        self.rExp << (self.rFunctionCall |
                      self.tConstant |
                      self.tId("name").setParseAction(self.lookup_id_action) |
                      Group(Suppress("(") + self.rNumExp + Suppress(")")) |
                      Group("+" + self.rExp) |
                      Group("-" + self.rExp)).setParseAction(lambda x : x[0])
        self.rMulExp << ((self.rExp + ZeroOrMore(self.tMulOp + self.rExp))).setParseAction(self.mulexp_action)
        self.rNumExp << (self.rMulExp + ZeroOrMore(self.tAddOp + self.rMulExp)).setParseAction(self.numexp_action)

        #Definitions of rules for logical expressions (these are without parenthesis support)
        self.rAndExp = Forward()
        self.rLogExp = Forward()
        self.rRelExp = (self.rNumExp + self.tRelOp + self.rNumExp).setParseAction(self.relexp_action)
        self.rAndExp << (self.rRelExp("exp") + ZeroOrMore(Literal("&&").setParseAction(self.andexp_action) +
                         self.rRelExp("exp")).setParseAction(lambda x : self.relexp_code))
        self.rLogExp << (self.rAndExp("exp") + ZeroOrMore(Literal("||").setParseAction(self.logexp_action) +
                         self.rAndExp("exp")).setParseAction(lambda x : self.andexp_code))

        #Definitions of rules for statements
        self.rStatement = Forward()
        self.rStatementList = Forward()
        self.rReturnStatement = (Keyword("return") + self.rNumExp("exp") +
                                 Suppress(";")).setParseAction(self.return_action)
        self.rAssignmentStatement = (self.tId("var") + Suppress("=") + self.rNumExp("exp") +
                                     Suppress(";")).setParseAction(self.assignment_action)
        self.rFunctionCallStatement = self.rFunctionCall + Suppress(";")
        self.rIfStatement = ( (Keyword("if") + FollowedBy("(")).setParseAction(self.if_begin_action) +
                              (Suppress("(") + self.rLogExp + Suppress(")")).setParseAction(self.if_body_action) +
                              (self.rStatement + Empty()).setParseAction(self.if_else_action) +
                              Optional(Keyword("else") + self.rStatement)).setParseAction(self.if_end_action)
        self.rWhileStatement = ( (Keyword("while") + FollowedBy("(")).setParseAction(self.while_begin_action) +
                                 (Suppress("(") + self.rLogExp + Suppress(")")).setParseAction(self.while_body_action) +
                                 self.rStatement).setParseAction(self.while_end_action)
        self.rCompoundStatement = Group(Suppress("{") + self.rStatementList + Suppress("}"))
        self.rStatement << (self.rReturnStatement | self.rIfStatement | self.rWhileStatement |
                            self.rFunctionCallStatement | self.rAssignmentStatement | self.rCompoundStatement)
        self.rStatementList << ZeroOrMore(self.rStatement)

        self.rLocalVariable = (self.tType("type") + self.tId("name") + FollowedBy(";")).setParseAction(self.local_variable_action)
        self.rLocalVariableList = ZeroOrMore(self.rLocalVariable + Suppress(";"))
        self.rFunctionBody = Suppress("{") + Optional(self.rLocalVariableList).setParseAction(self.function_body_action) + \
                             self.rStatementList + Suppress("}")
        self.rParameter = (self.tType("type") + self.tId("name")).setParseAction(self.parameter_action)
        self.rParameterList = delimitedList(self.rParameter)
        self.rFunction = ( (self.tType("type") + self.tId("name")).setParseAction(self.function_begin_action) +
                           Group(Suppress("(") + Optional(self.rParameterList)("params") + Suppress(")") +
                           self.rFunctionBody)).setParseAction(self.function_end_action)

        self.rFunctionList = OneOrMore(self.rFunction)
        self.rProgram = (Empty().setParseAction(self.data_begin_action) + self.rGlobalVariableList +
                         Empty().setParseAction(self.code_begin_action) + self.rFunctionList).setParseAction(self.program_end_action)

        #shared data
        self.shared = SharedData()
        #symbol table
        self.symtab = SymbolTable(self.shared)
        #code generator
        self.codegen = CodeGenerator(self.shared, self.symtab)

        #index of the current function call
        self.function_call_index = -1
        #stack for the nested function calls
        self.function_call_stack = []
        #arguments of the current function call
        self.function_arguments = []
        #stack for arguments of the nested function calls
        self.function_arguments_stack = []
        #number of arguments for the curent function call
        self.function_arguments_number = -1
        #stack for the number of arguments for the nested function calls
        self.function_arguments_number_stack = []

        #last relational expression
        self.relexp_code = None
        #last and expression
        self.andexp_code = None
        #label number for "false" internal labels
        self.false_label_number = -1
        #label number for all other internal labels
        self.label_number = None
        #label stack for nested statements
        self.label_stack = []

    def warning(self, message, print_location=True):
        """Displays warning message. Uses exshared for current location of parsing"""
        msg = "Warning"
        if print_location and (exshared.location != None):
            wline = lineno(exshared.location, exshared.text)
            wcol = col(exshared.location, exshared.text)
            wtext = line(exshared.location, exshared.text)
            msg += " at line %d, col %d" % (wline, wcol)
        msg += ": %s" % message
        if print_location and (exshared.location != None):
            msg += "\n%s" % wtext
        print(msg)


    def data_begin_action(self):
        """Inserts text at start of data segment"""
        self.codegen.prepare_data_segment()

    def code_begin_action(self):
        """Inserts text at start of code segment"""
        self.codegen.prepare_code_segment()

    def global_variable_action(self, text, loc, var):
        """Code executed after recognising a global variable"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("GLOBAL_VAR:",var)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        index = self.symtab.insert_global_var(var.name, var.type)
        self.codegen.global_var(var.name)
        return index

    def local_variable_action(self, text, loc, var):
        """Code executed after recognising a local variable"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("LOCAL_VAR:",var, var.name, var.type)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        index = self.symtab.insert_local_var(var.name, var.type, self.shared.function_vars)
        self.shared.function_vars += 1
        return index

    def parameter_action(self, text, loc, par):
        """Code executed after recognising a parameter"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("PARAM:",par)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        index = self.symtab.insert_parameter(par.name, par.type)
        self.shared.function_params += 1
        return index

    def constant_action(self, text, loc, const):
        """Code executed after recognising a constant"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("CONST:",const)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        return self.symtab.insert_constant(const[0], const[1])

    def function_begin_action(self, text, loc, fun):
        """Code executed after recognising a function definition (type and function name)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("FUN_BEGIN:",fun)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        self.shared.function_index = self.symtab.insert_function(fun.name, fun.type)
        self.shared.function_name = fun.name
        self.shared.function_params = 0
        self.shared.function_vars = 0
        self.codegen.function_begin();

    def function_body_action(self, text, loc, fun):
        """Code executed after recognising the beginning of function's body"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("FUN_BODY:",fun)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        self.codegen.function_body()

    def function_end_action(self, text, loc, fun):
        """Code executed at the end of function definition"""
        if DEBUG > 0:
            print("FUN_END:",fun)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #set function's attribute to number of function parameters
        self.symtab.set_attribute(self.shared.function_index, self.shared.function_params)
        #clear local function symbols (but leave function name)
        self.symtab.clear_symbols(self.shared.function_index + 1)
        self.codegen.function_end()

    def return_action(self, text, loc, ret):
        """Code executed after recognising a return statement"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("RETURN:",ret)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        if not self.symtab.same_types(self.shared.function_index, ret.exp[0]):
            raise SemanticException("Incompatible type in return")
        #set register for function's return value to expression value
        reg = self.codegen.take_function_register()
        self.codegen.move(ret.exp[0], reg)
        #after return statement, register for function's return value is available again
        self.codegen.free_register(reg)
        #jump to function's exit
        self.codegen.unconditional_jump(self.codegen.label(self.shared.function_name+"_exit", True))

    def lookup_id_action(self, text, loc, var):
        """Code executed after recognising an identificator in expression"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("EXP_VAR:",var)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        var_index = self.symtab.lookup_symbol(var.name, [SharedData.KINDS.GLOBAL_VAR, SharedData.KINDS.PARAMETER, SharedData.KINDS.LOCAL_VAR])
        if var_index == None:
            raise SemanticException("'%s' undefined" % var.name)
        return var_index

    def assignment_action(self, text, loc, assign):
        """Code executed after recognising an assignment statement"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("ASSIGN:",assign)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        var_index = self.symtab.lookup_symbol(assign.var, [SharedData.KINDS.GLOBAL_VAR, SharedData.KINDS.PARAMETER, SharedData.KINDS.LOCAL_VAR])
        if var_index == None:
            raise SemanticException("Undefined lvalue '%s' in assignment" % assign.var)
        if not self.symtab.same_types(var_index, assign.exp[0]):
            raise SemanticException("Incompatible types in assignment")
        self.codegen.move(assign.exp[0], var_index)

    def mulexp_action(self, text, loc, mul):
        """Code executed after recognising a mulexp expression (something *|/ something)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("MUL_EXP:",mul)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #iterate through all multiplications/divisions
        m = list(mul)
        while len(m) > 1:
            if not self.symtab.same_types(m[0], m[2]):
                raise SemanticException("Invalid opernads to binary '%s'" % m[1])
            reg = self.codegen.arithmetic(m[1], m[0], m[2])
            #replace first calculation with it's result
            m[0:3] = [reg]
        return m[0]

    def numexp_action(self, text, loc, num):
        """Code executed after recognising a numexp expression (something +|- something)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("NUM_EXP:",num)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #iterate through all additions/substractions
        n = list(num)
        while len(n) > 1:
            if not self.symtab.same_types(n[0], n[2]):
                raise SemanticException("Invalid opernads to binary '%s'" % n[1])
            reg = self.codegen.arithmetic(n[1], n[0], n[2])
            #replace first calculation with it's result
            n[0:3] = [reg]
        return n[0]

    def function_call_prepare_action(self, text, loc, fun):
        """Code executed after recognising a function call (type and function name)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("FUN_PREP:",fun)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        index = self.symtab.lookup_symbol(fun.name, SharedData.KINDS.FUNCTION)
        if index == None:
            raise SemanticException("'%s' is not a function" % fun.name)
        #save any previous function call data (for nested function calls)
        self.function_call_stack.append(self.function_call_index)
        self.function_call_index = index
        self.function_arguments_stack.append(self.function_arguments[:])
        del self.function_arguments[:]
        self.codegen.save_used_registers()

    def argument_action(self, text, loc, arg):
        """Code executed after recognising each of function's arguments"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("ARGUMENT:",arg.exp)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        arg_ordinal = len(self.function_arguments)
        #check argument's type
        if not self.symtab.same_type_as_argument(arg.exp, self.function_call_index, arg_ordinal):
            raise SemanticException("Incompatible type for argument %d in '%s'" % (arg_ordinal + 1, self.symtab.get_name(self.function_call_index)))
        self.function_arguments.append(arg.exp)

    def function_call_action(self, text, loc, fun):
        """Code executed after recognising the whole function call"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("FUN_CALL:",fun)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #check number of arguments
        if len(self.function_arguments) != self.symtab.get_attribute(self.function_call_index):
            raise SemanticException("Wrong number of arguments for function '%s'" % fun.name)
        #arguments should be pushed to stack in reverse order
        self.function_arguments.reverse()
        self.codegen.function_call(self.function_call_index, self.function_arguments)
        self.codegen.restore_used_registers()
        return_type = self.symtab.get_type(self.function_call_index)
        #restore previous function call data
        self.function_call_index = self.function_call_stack.pop()
        self.function_arguments = self.function_arguments_stack.pop()
        register = self.codegen.take_register(return_type)
        #move result to a new free register, to allow the next function call
        self.codegen.move(self.codegen.take_function_register(return_type), register)
        return register

    def relexp_action(self, text, loc, arg):
        """Code executed after recognising a relexp expression (something relop something)"""
        if DEBUG > 0:
            print("REL_EXP:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        exshared.setpos(loc, text)
        if not self.symtab.same_types(arg[0], arg[2]):
            raise SemanticException("Invalid operands for operator '{0}'".format(arg[1]))
        self.codegen.compare(arg[0], arg[2])
        #return relational operator's code
        self.relexp_code = self.codegen.relop_code(arg[1], self.symtab.get_type(arg[0]))
        return self.relexp_code

    def andexp_action(self, text, loc, arg):
        """Code executed after recognising a andexp expression (something and something)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("AND+EXP:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        label = self.codegen.label("false{0}".format(self.false_label_number), True, False)
        self.codegen.jump(self.relexp_code, True, label)
        self.andexp_code = self.relexp_code
        return self.andexp_code

    def logexp_action(self, text, loc, arg):
        """Code executed after recognising logexp expression (something or something)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("LOG_EXP:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        label = self.codegen.label("true{0}".format(self.label_number), True, False)
        self.codegen.jump(self.relexp_code, False, label)
        self.codegen.newline_label("false{0}".format(self.false_label_number), True, True)
        self.false_label_number += 1

    def if_begin_action(self, text, loc, arg):
        """Code executed after recognising an if statement (if keyword)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("IF_BEGIN:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        self.false_label_number += 1
        self.label_number = self.false_label_number
        self.codegen.newline_label("if{0}".format(self.label_number), True, True)

    def if_body_action(self, text, loc, arg):
        """Code executed after recognising if statement's body"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("IF_BODY:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #generate conditional jump (based on last compare)
        label = self.codegen.label("false{0}".format(self.false_label_number), True, False)
        self.codegen.jump(self.relexp_code, True, label)
        #generate 'true' label (executes if condition is satisfied)
        self.codegen.newline_label("true{0}".format(self.label_number), True, True)
        #save label numbers (needed for nested if/while statements)
        self.label_stack.append(self.false_label_number)
        self.label_stack.append(self.label_number)

    def if_else_action(self, text, loc, arg):
        """Code executed after recognising if statement's else body"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("IF_ELSE:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #jump to exit after all statements for true condition are executed
        self.label_number = self.label_stack.pop()
        label = self.codegen.label("exit{0}".format(self.label_number), True, False)
        self.codegen.unconditional_jump(label)
        #generate final 'false' label (executes if condition isn't satisfied)
        self.codegen.newline_label("false{0}".format(self.label_stack.pop()), True, True)
        self.label_stack.append(self.label_number)

    def if_end_action(self, text, loc, arg):
        """Code executed after recognising a whole if statement"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("IF_END:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        self.codegen.newline_label("exit{0}".format(self.label_stack.pop()), True, True)

    def while_begin_action(self, text, loc, arg):
        """Code executed after recognising a while statement (while keyword)"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("WHILE_BEGIN:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        self.false_label_number += 1
        self.label_number = self.false_label_number
        self.codegen.newline_label("while{0}".format(self.label_number), True, True)

    def while_body_action(self, text, loc, arg):
        """Code executed after recognising while statement's body"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("WHILE_BODY:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #generate conditional jump (based on last compare)
        label = self.codegen.label("false{0}".format(self.false_label_number), True, False)
        self.codegen.jump(self.relexp_code, True, label)
        #generate 'true' label (executes if condition is satisfied)
        self.codegen.newline_label("true{0}".format(self.label_number), True, True)
        self.label_stack.append(self.false_label_number)
        self.label_stack.append(self.label_number)

    def while_end_action(self, text, loc, arg):
        """Code executed after recognising a whole while statement"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("WHILE_END:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        #jump to condition checking after while statement body
        self.label_number = self.label_stack.pop()
        label = self.codegen.label("while{0}".format(self.label_number), True, False)
        self.codegen.unconditional_jump(label)
        #generate final 'false' label and exit label
        self.codegen.newline_label("false{0}".format(self.label_stack.pop()), True, True)
        self.codegen.newline_label("exit{0}".format(self.label_number), True, True)

    def program_end_action(self, text, loc, arg):
        """Checks if there is a 'main' function and the type of 'main' function"""
        exshared.setpos(loc, text)
        if DEBUG > 0:
            print("PROGRAM_END:",arg)
            if DEBUG == 2: self.symtab.display()
            if DEBUG > 2: return
        index = self.symtab.lookup_symbol("main",SharedData.KINDS.FUNCTION)
        if index == None:
            raise SemanticException("Undefined reference to 'main'", False)
        elif self.symtab.get_type(index) != SharedData.TYPES.INT:
            self.warning("Return type of 'main' is not int", False)

    def parse_text(self,text):
        """Parse string (helper function)"""
        try:
            return self.rProgram.ignore(cStyleComment).parseString(text, parseAll=True)
        except SemanticException as err:
            print(err)
            exit(3)
        except ParseException as err:
            print(err)
            exit(3)

    def parse_file(self,filename):
        """Parse file (helper function)"""
        try:
            return self.rProgram.ignore(cStyleComment).parseFile(filename, parseAll=True)
        except SemanticException as err:
            print(err)
            exit(3)
        except ParseException as err:
            print(err)
            exit(3)

##########################################################################################
##########################################################################################
if 0:
    #main program
    mc = MicroC()
    output_file = "output.asm"

    if len(argv) == 1:
        input_file = stdin
    elif len(argv) == 2:
        input_file = argv[1]
    elif len(argv) == 3:
        input_file = argv[1]
        output_file = argv[2]
    else:
        usage = """Usage: {0} [input_file [output_file]]
    If output file is omitted, output.asm is used
    If input file is omitted, stdin is used""".format(argv[0])
        print(usage)
        exit(1)
    try:
        parse = stdin if input_file == stdin else open(input_file,'r')
    except Exception:
        print("Input file '%s' open error" % input_file)
        exit(2)
    mc.parse_file(parse)
    #if you want to see the final symbol table, uncomment next line
    #mc.symtab.display()
    try:
        out = open(output_file, 'w')
        out.write(mc.codegen.code)
        out.close
    except Exception:
        print("Output file '%s' open error" % output_file)
        exit(2)

##########################################################################################
##########################################################################################

if __name__ == "__main__":

    test_program_example = """
        int a;
        int b;
        int c;
        unsigned d;

        int fun1(int x, unsigned y) {
            return 123;
        }

        int fun2(int a) {
            return 1 + a * fun1(a, 456u);
        }

        int main(int x, int y) {
            int w;
            unsigned z;
            if (9 > 8 && 2 < 3 || 6 != 5 && a <= b && c < x || w >= y) {
                a = b + 1;
                if (x == y)
                    while (d < 4u)
                        x = x * w;
                else
                    while (a + b < c - y && x > 3 || y < 2)
                        if (z > d)
                            a = a - 4;
                        else
                            b = a * b * c * x / y;
            }
            else
                c = 4;
            a = fun1(x,d) + fun2(fun1(fun2(w + 3 * 2) + 2 * c, 2u));
            return 2;
        }
    """

    mc = MicroC()
    mc.parse_text(test_program_example)
    print(mc.codegen.code)
