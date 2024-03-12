from pyparsing import *

text = """Lorem ipsum dolor sit amet, consectetur adipisicing
elit, sed do eiusmod tempor incididunt ut labore et dolore magna
aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis
aute irure dolor in reprehenderit in voluptate velit esse cillum
dolore eu fugiat nulla pariatur. Excepteur sint occaecat
cupidatat non proident, sunt in culpa qui officia deserunt
mollit anim id est laborum"""

# find all words beginning with a vowel
vowels = "aeiouAEIOU"
initialVowelWord = Word(vowels,alphas)

# Unfortunately, searchString will advance character by character through
# the input text, so it will detect that the initial "Lorem" is not an
# initialVowelWord, but then it will test "orem" and think that it is. So
# we need to add a do-nothing term that will match the words that start with
# consonants, but we will just throw them away when we match them. The key is
# that, in having been matched, the parser will skip over them entirely when
# looking for initialVowelWords.
consonants = ''.join(c for c in alphas if c not in vowels)
initialConsWord = Word(consonants, alphas).suppress()

# using scanString to locate where tokens are matched
for t,start,end in (initialConsWord|initialVowelWord).scanString(text):
    if t:
        print(start,':', t[0])

# add parse action to annotate the parsed tokens with their location in the
# input string
def addLocnToTokens(s,l,t):
    t['locn'] = l
    t['word'] = t[0]
initialVowelWord.setParseAction(addLocnToTokens)

for ivowelInfo in (initialConsWord | initialVowelWord).searchString(text):
    if not ivowelInfo:
        continue
    print(ivowelInfo.locn, ':', ivowelInfo.word)


# alternative - add an Empty that will save the current location
def location(name):
    return Empty().setParseAction(lambda s,l,t: t.__setitem__(name,l))
locateInitialVowels = location("locn") + initialVowelWord("word")

# search through the input text
for ivowelInfo in (initialConsWord | locateInitialVowels).searchString(text):
    if not ivowelInfo:
        continue
    print(ivowelInfo.locn, ':', ivowelInfo.word)
