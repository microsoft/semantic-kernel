# vim:fileencoding=utf-8
#
# greetingInKorean.py
#
# Demonstration of the parsing module, on the prototypical "Hello, World!" example
#
# Copyright 2004-2016, by Paul McGuire
#
from pyparsing import Word, pyparsing_unicode as ppu

koreanChars = ppu.Korean.alphas
koreanWord = Word(koreanChars, min=2)

# define grammar
greet = koreanWord + "," + koreanWord + "!"

# input string
hello = '안녕, 여러분!' #"Hello, World!" in Korean

# parse input string
print(greet.parseString(hello))
