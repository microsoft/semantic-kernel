# CONTRIBUTING

Thank you for your interest in working on pyparsing! Pyparsing has become a popular module for creating simple
text parsing and data scraping applications. It has been incorporated in several widely-used packages, and is
often used by beginners as part of their first Python project.

## Raising questions / asking for help

If you have a question on using pyparsing, there are a number of resources available online.

- [StackOverflow](https://stackoverflow.com/questions/tagged/pyparsing) - about 10 years of SO questions and answers
  can be searched on StackOverflow, tagged with the `pyparsing` tag. Note that some of the older posts will refer
  to features in Python 2, or to versions and coding practices for pyparsing that have been replaced by newer classes
  and coding idioms.

- [pyparsing sub-reddit](https://www.reddit.com/r/pyparsing/) - still very lightly attended, but open to anyone
  wishing to post questions or links related to pyparsing. An alternative channel to StackOverflow for asking
  questions.

- [online docs](https://pyparsing-docs.readthedocs.io/en/latest/index.html) and a separately maintained set of class
  library docs [here](https://pyparsing-doc.neocities.org/) - These docs are auto-generated from the docstrings
  embedded in the pyparsing classes, so they can also be viewed in the interactive Python console's and Jupyter
  Notebook's `help` commands.

- [the pyparsing Wikispaces archive](https://github.com/pyparsing/wikispaces_archive) - Before hosting on GitHub,
  pyparsing had a separate wiki on the wikispaces.com website. In 2018 this page was discontinued. The discussion
  content archive has been reformatted into Markdown and can be viewed by year at the GitHub repository. Just as
  with some of the older questions on StackOverflow, some of these older posts may reflect out-of-date pyparsing
  and Python features.

- [submit an issue](https://github.com/pyparsing/pyparsing/issues) - If you have a problem with pyparsing that looks
  like an actual bug, or have an idea for a feature to add to pyaprsing please submit an issue on GitHub. Some
  pyparsing behavior may be counter-intuitive, so try to review some of the other resources first, or some of the
  other open and closed issues. Or post your question on SO or reddit. But don't wait until you are desperate and
  frustrated - just ask! :)


## Submitting changes

If you are considering proposing updates to pyparsing, please bear in mind the following guidelines.

Please review [_The Zen of Pyparsing_ and _The Zen of Pyparsing 
Development_](https://github.com/pyparsing/pyparsing/wiki/Zen) 
article on the pyparsing wiki, to get a general feel for the historical and future approaches to pyparsing's 
design, and intended developer experience as an embedded DSL.

## Some design points

- Minimize additions to the module namespace. Over time, pyparsing's namespace has acquired a *lot* of names. 
  New features have been encapsulated into namespace classes to try to hold back the name flooding when importing 
  pyparsing.

- New operator overloads will need to show broad applicability.

- Performance tuning should focus on parse time performance. Optimizing parser definition performance is secondary.

- New external dependencies will require substantial justification, and if included, will need to be guarded for 
  `ImportError`s raised if the external module is not installed.

## Some coding points

These coding styles are encouraged whether submitting code for core pyparsing or for submitting an example.

- PEP8 - at this time, pyparsing is very non-compliant with many PEP8 guidelines, especially those regarding
  name casing. I had just finished several years of Java and Smalltalk development, and camel case seemed to be the
  future trend in coding styles. There are plans to convert these names to PEP8-conformant snake case, but this will
  be done over several releases to provide a migration path for current pyparsing-dependent applications. See more
  information at the [PEP8 wiki page](https://github.com/pyparsing/pyparsing/wiki/PEP-8-planning).
  
  If you wish to submit a new example, please follow PEP8 name and coding guidelines. Example code must be available
  for distribution with the rest of pyparsing under the MIT open source license.

- No backslashes for line continuations.
  Continuation lines for expressions in ()'s should start with the continuing operator:

      really_long_line = (something
                          + some_other_long_thing
                          + even_another_long_thing)

- Changes to core pyparsing must be compatible back to Py3.5 without conditionalizing. Later Py3 features may be
  used in examples by way of illustration.

- str.format() statements should use named format arguments (unless this proves to be a slowdown at parse time).

- List, tuple, and dict literals should include a trailing comma after the last element, which reduces changeset 
  clutter when another element gets added to the end.

- Examples should import pyparsing and the common namespace classes as:

      import pyparsing as pp
      # if necessary
      ppc = pp.pyparsing_common
      ppu = pp.pyparsing_unicode

- Where possible use operators to create composite parse expressions:

      expr = expr_a + expr_b | expr_c
      
  instead of:
  
      expr = pp.MatchFirst([pp.And([expr_a, expr_b]), expr_c])

  Exception: if using a generator to create an expression:
  
      import keyword
      python_keywords = keyword.kwlist
      any_keyword = pp.MatchFirst(pp.Keyword(kw) 
                                  for kw in python_keywords))

- Learn [The Classic Blunders](https://github.com/pyparsing/pyparsing/wiki/The-Classic-Blunders) and 
  how to avoid them when developing new examples.

- New features should be accompanied with updates to unitTests.py and a bullet in the CHANGES file.
