# removeLineBreaks.py
#
# Demonstration of the pyparsing module, converting text files
# with hard line-breaks to text files with line breaks only
# between paragraphs.  (Helps when converting downloads from Project
# Gutenberg - https://www.gutenberg.org/ - to import to word processing apps
# that can reformat paragraphs once hard line-breaks are removed.)
#
# Uses parse actions and transformString to remove unwanted line breaks,
# and to double up line breaks between paragraphs.
#
# Copyright 2006, by Paul McGuire
#
import pyparsing as pp

line_end = pp.LineEnd()

# define an expression for the body of a line of text - use a predicate condition to
# accept only lines with some content.
def mustBeNonBlank(t):
    return t[0] != ''
    # could also be written as
    # return bool(t[0])

lineBody = pp.SkipTo(line_end).addCondition(mustBeNonBlank, message="line body can't be empty")

# now define a line with a trailing lineEnd, to be replaced with a space character
textLine = lineBody + line_end().setParseAction(pp.replaceWith(" "))

# define a paragraph, with a separating lineEnd, to be replaced with a double newline
para = pp.OneOrMore(textLine) + line_end().setParseAction(pp.replaceWith("\n\n"))

# run a test
test = """
    Now is the
    time for
    all
    good men
    to come to

    the aid of their
    country.
"""
print(para.transformString(test))

# process an entire file
#   Project Gutenberg EBook of Successful Methods of Public Speaking, by Grenville Kleiser
#   Download from http://www.gutenberg.org/cache/epub/18095/pg18095.txt
#
with open("18095-8.txt") as source_file:
    original = source_file.read()

# use transformString to convert line breaks
transformed = para.transformString(original)

with open("18095-8_reformatted.txt", "w") as transformed_file:
    transformed_file.write(transformed)
