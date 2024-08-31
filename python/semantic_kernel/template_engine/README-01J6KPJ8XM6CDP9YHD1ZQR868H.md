---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:56:16Z
---

# Prompt Template Engine

The Semantic Kernel uses the following grammar to parse prompt templates:

```clj {"id":"01J6KPYGBX0RZP59NQYJF695ZB"}
# BNF parsed by TemplateTokenizer
[template]       ::= "" | [block] | [block] [template]
[block]          ::= [sk-block] | [text-block]
[sk-block]       ::= "{{" [variable] "}}" | "{{" [value] "}}" | "{{" [function-call] "}}"
[text-block]     ::= [any-char] | [any-char] [text-block]
[any-char]       ::= any char

# BNF parsed by CodeTokenizer:
[template]       ::= "" | [variable] " " [template] | [value] " " [template] | [function-call] " " [template]
[variable]       ::= "$" [valid-name]
[value]          ::= "'" [text] "'" | '"' [text] '"'
[function-call]  ::= [function-id] | [function-id] [parameter]
[parameter]      ::= [variable] | [value]

# BNF parsed by dedicated blocks
[function-id]    ::= [valid-name] | [valid-name] "." [valid-name]
[valid-name]     ::= [valid-symbol] | [valid-symbol] [valid-name]
[valid-symbol]   ::= [letter] | [digit] | "_"
[letter]         ::= "a" | "b" ... | "z" | "A" | "B" ... | "Z"
[digit]          ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

# Ran on 2024-08-31 07:56:14Z for 1.44s exited with 0
# BNF parsed by TemplateTokenizer
[template]       ::= "" | [block] | [block] [template]
[block]          ::= [sk-block] | [text-block]
[sk-block]       ::= "{{" [variable] "}}" | "{{" [value] "}}" | "{{" [function-call] "}}"
[text-block]     ::= [any-char] | [any-char] [text-block]
[any-char]       ::= any char

# BNF parsed by CodeTokenizer:
[template]       ::= "" | [variable] " " [template] | [value] " " [template] | [function-call] " " [template]
[variable]       ::= "$" [valid-name]
[value]          ::= "'" [text] "'" | '"' [text] '"'
[function-call]  ::= [function-id] | [function-id] [parameter]
[parameter]      ::= [variable] | [value]

# BNF parsed by dedicated blocks
[function-id]    ::= [valid-name] | [valid-name] "." [valid-name]
[valid-name]     ::= [valid-symbol] | [valid-symbol] [valid-name]
[valid-symbol]   ::= [letter] | [digit] | "_"
[letter]         ::= "a" | "b" ... | "z" | "A" | "B" ... | "Z"
[digit]          ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```
