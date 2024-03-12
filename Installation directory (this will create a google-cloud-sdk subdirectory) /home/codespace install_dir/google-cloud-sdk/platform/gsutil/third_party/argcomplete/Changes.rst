Changes for v1.9.4 (2018-02-13)
===============================

-  Use the correct interpreter when checking wrappers (#226)

-  Provide shellcode as a module function (#237)

Changes for v1.9.3 (2017-11-16)
===============================

-  Fix handling of COMP\_POINT (#236)

-  Fix crash when writing unicode to debug\_stream in Python 2 (#230)

Changes for v1.9.2 (2017-08-23)
===============================

-  Fix release

Changes for v1.9.1 (2017-08-23)
===============================

-  Fix release

Changes for v1.9.0 (2017-08-23)
===============================

-  Add SuppressCompleter to skip completion for specific arguments while
   allowing help text (#224)

-  Redirect all output to debug stream in debug mode (#206)

-  Complete python -m module (#204)

Changes for v1.8.2 (2017-01-26)
===============================

-  Fix bug introduced in v0.7.1 where completers would not receive the
   parser keyword argument.

-  Documentation improvements.

Changes for v1.8.1 (2017-01-21)
===============================

-  Fix completion after tokens with wordbreak chars (#197)

Changes for v1.8.0 (2017-01-19)
===============================

This release contains work by @evanunderscore with numerous improvements
to the handling of special characters in completions.

-  Simplify nospace handling in global completion (#195)

-  Specially handle all characters in COMP\_WORDBREAKS (#187)

-  Use setuptools tests-require directive, fixes #186

-  Complete files using the specified interpreter (#192)

-  Fix completion for scripts run via python (#191)

-  Clarify argument to register-python-argcomplete (#190)

-  Fix handling of commas and other special chars (#172); handle more
   special characters (#189)

-  Fix handling of special characters in tcsh (#188)

-  Update my\_shlex to Python 3.6 version (#184)

-  Fix additional trailing space in exact matches (#183)

-  Adjust tests to handle development environments (#180)

-  Fix tcsh tests on OSX (#177); Update bash on OSX (#176); Check output
   of test setup command (#179)

-  Optionally disable duplicated flags (#143)

-  Add default\_completer option to CompletionFinder.\ **call** (#167)

-  Let bash add or suppress trailing space (#159)

Changes for v1.7.0 (2016-11-30)
===============================

-  Restore parser to its original state to allow reuse after completion
   (#150).

-  Expose COMP\_TYPE environment variable (#157). Thanks to Matt Clay
   (@mattclay).

-  Test infrastructure and documentation improvements.

Changes for v1.6.0 (2016-10-20)
===============================

-  Add support for tcsh (#155)

-  Fix handling of unquoted completions containing $ (#154)

-  Don't insert unnecessary leading quote char in completions (#152)

-  Fix parser reuse with positional arguments (#149)

-  Tests: Add simple pexpect tests for bash (#153); Add test case to
   verify #20 is fixed (#148)

-  Thanks to @davvid and @evanunderscore for their work on this release.

Changes for v1.5.1 (2016-10-11)
===============================

-  Packaging fix

Changes for v1.5.0 (2016-10-11)
===============================

-  Do not suggest options from mutually exclusive groups (#145).

Version 1.4.1 (2016-06-14)
==========================
- activate-global-python-argcomplete runs on Homebrew out of the box

Version 1.4.0 (2016-06-10)
==========================
- Correctly handle suggestions for positionals with variable-length nargs. Thanks to @evanunderscore (#132, #133).

Version 1.3.0 (2016-06-01)
==========================
- Correctly handle suggestions with custom nargs for optionals. Thanks to @evanunderscore (#131).

Version 1.2.0 (2016-05-25)
==========================
- Fix propagation of partially parsed subparser namespace into parent parser namespace upon subparser failure due to
  partial args. This allows completers to access partial parse results for subparser optionals in parsed_args (#114).
- The default completer can now be specified when manually instantiating CompletionFinder. Thanks to @avylove (#130).

Version 1.1.1 (2016-03-22)
==========================
- Use FilesCompleter as default completer fallback (#120).

Version 1.1.0 (2016-02-21)
==========================
- Recognize subclasses of argparse._SubParsersAction. Thanks to Stephen Koo (#118).
- Support parsed_args in custom completers with missing args. Thanks to Dan Kilman (#124).
- Non-ASCII support in FilesCompleter.
- Automatically enable FilesCompleter for argparse.FileType arguments.

Version 1.0.0 (2015-08-22)
==========================
- Don't print args with suppressed help by default; add
  ``argcomplete.autocomplete(print_suppressed=True)`` to control this
  behavior (#113).

Version 0.9.0 (2015-07-03)
==========================
- Fix always_complete_options=False support (#115).

Version 0.8.9 (2015-06-01)
==========================
- Correct doc filename in setup.cfg (fixes bdist_rpm failure, Issue 111).
- Make context managers exception-safe. Thanks to Mikołaj Siedlarek (pull request #110).

Version 0.8.8 (2015-05-01)
==========================
- Build and upload universal wheel packages in release.
- Fix issue with non-string choices for arguments. Thanks to @neizod (pull request #107).
- Improve non-ascii argparse argument support on Python 2.7.

Version 0.8.7 (2015-04-11)
==========================
- register-python-argcomplete: add option to avoid default readline completion. Thanks to @drmalex07 (pull request #99).

Version 0.8.6 (2015-04-11)
==========================
- Expand tilde in script name, allowing argcomplete to work when invoking scripts from one's home directory. Thanks to @VorpalBlade (Issue 104).

Version 0.8.5 (2015-04-07)
==========================
- Fix issues related to using argcomplete in a REPL environement.
- New helper method for custom completion display.
- Expand test suite; formatting cleanup.

Version 0.8.4 (2014-12-11)
==========================
- Fix issue related to using argcomplete in a REPL environement. Thanks to @wapiflapi (pull request #91).

Version 0.8.3 (2014-11-09)
==========================
- Fix multiple issues related to using argcomplete in a REPL environement. Thanks to @wapiflapi (pull request #90).

Version 0.8.2 (2014-11-03)
==========================
- Don't strip colon prefix in completion results if COMP_WORDBREAKS does not contain a colon. Thanks to @berezv (pull request #88).

Version 0.8.1 (2014-07-02)
==========================
- Use complete --nospace to avoid issues with directory completion.

Version 0.8.0 (2014-04-07)
==========================
- Refactor main body of code into a class to enable subclassing and overriding of functionality (Issue #78).

Version 0.7.1 (2014-03-29)
==========================
- New keyword option "argcomplete.autocomplete(validator=...)" to supply a custom validator or bypass default validation. Thanks to @thijsdezoete (Issue #77).
- Document debug options.

Version 0.7.0 (2014-01-19)
==========================
- New keyword option "argcomplete.autocomplete(exclude=[...])" to suppress options (Issue #74).
- More speedups to code path for global completion hook negative result.

Version 0.6.9 (2014-01-19)
==========================
- Fix handling of development mode script wrappers. Thanks to @jmlopez-rod and @dcosson (Issue #69).
- Speed up code path for global completion hook negative result by loading pkg_resources on demand.

Version 0.6.8 (2014-01-18)
==========================
- Begin tracking changes in changelog.
- Add completion support for PBR installed scripts (PR #71).
- Detect easy-install shims with shebang lines that contain Py instead of py (Issue #69).
