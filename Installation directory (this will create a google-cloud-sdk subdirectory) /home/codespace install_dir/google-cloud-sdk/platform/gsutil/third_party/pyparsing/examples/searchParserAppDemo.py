from searchparser import SearchQueryParser

products = [ "grape juice", "grape jelly", "orange juice", "orange jujubees",
    "strawberry jam", "prune juice", "prune butter", "orange marmalade",
    "grapefruit juice" ]

class FruitSearchParser(SearchQueryParser):
    def GetWord(self, word):
        return { p for p in products if p.startswith(word + " ") }

    def GetWordWildcard(self, word):
        return { p for p in products if p.startswith(word[:-1]) }

    def GetQuotes(self, search_string, tmp_result):
        result = set()
        # I have no idea how to use this feature...
        return result

    def GetNot(self, not_set):
        return set( products ) - not_set


parser = FruitSearchParser()

tests = """\
    grape or orange
    grape*
    not(grape*)
    prune and grape""".splitlines()

for t in tests:
    print(t.strip())
    print(parser.Parse(t))
    print('')
