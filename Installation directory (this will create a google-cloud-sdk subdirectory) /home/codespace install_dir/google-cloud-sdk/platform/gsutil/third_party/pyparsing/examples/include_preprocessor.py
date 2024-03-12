#
# include_preprocessor.py
#
# Short pyparsing script to perform #include inclusions similar to the C preprocessor
#
# Copyright 2019, Paul McGuire
#
import pyparsing as pp
from pathlib import Path

# parser elements to be used to assemble into #include parser
SEMI = pp.Suppress(';')
INCLUDE = pp.Keyword("#include")
quoted_string = pp.quotedString.addParseAction(pp.removeQuotes)
file_ref = (quoted_string
            | pp.Word(pp.printables, excludeChars=';'))

# parser for parsing "#include xyz.dat;" directives
include_directive = (INCLUDE + file_ref("include_file_name") + SEMI)

# add parse action that will recursively pull in included files - when
# using transformString, the value returned from the parse action will replace
# the text matched by the attached expression
seen = set()
def read_include_contents(s, l, t):
    include_file_ref = t.include_file_name
    include_echo = "/* {} */".format(pp.line(l, s).strip())

    # guard against recursive includes
    if include_file_ref not in seen:
        seen.add(include_file_ref)
        included_file_contents = Path(include_file_ref).read_text()
        return (include_echo + '\n'
                + include_directive.transformString(included_file_contents))
    else:
        lead = ' '*(pp.col(l, s) - 1)
        return "/* recursive include! */\n{}{}".format(lead, include_echo)

# attach include processing method as parse action (parse-time callback)
# to include_directive expression
include_directive.addParseAction(read_include_contents)


if __name__ == '__main__':

    # demo

    # create test files:
    # - a.txt includes b.txt
    # - b.txt includes c.txt
    # - c.txt includes b.txt (must catch infinite recursion)
    Path('a.txt').write_text("""\
        /* a.txt */
        int i;
    
        /* sometimes included files aren't in quotes */    
        #include b.txt;
        """)

    Path('b.txt').write_text("""\
        i = 100;
        #include 'c.txt';
        """)

    Path('c.txt').write_text("""\
        i += 1;
        
        /* watch out! this might be recursive if this file included by b.txt */
        #include b.txt;
        """)


    # use include_directive.transformString to perform includes

    # read contents of original file
    initial_file = Path('a.txt').read_text()

    # print original file
    print(initial_file)
    print('-----------------')

    # expand includes in source file (and any included files) and print the result
    expanded_source = include_directive.transformString(initial_file)
    print(expanded_source)

    # clean up
    for fname in "a.txt b.txt c.txt".split():
        Path(fname).unlink()
