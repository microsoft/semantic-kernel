# Contribution Guidelines

If you’re reading this, you’re probably interested in contributing to Charset Normalizer. 
Thank you very much! Open source projects live-and-die based on the support they receive from others, 
and the fact that you’re even considering contributing to this project is very generous of you.

## Questions

The GitHub issue tracker is for *bug reports* and *feature requests*. 
Questions are allowed only when no answer are provided in docs.

## Good Bug Reports

Please be aware of the following things when filing bug reports:

1. Avoid raising duplicate issues. *Please* use the GitHub issue search feature
   to check whether your bug report or feature request has been mentioned in
   the past. Duplicate bug reports and feature requests are a huge maintenance
   burden on the limited resources of the project. If it is clear from your
   report that you would have struggled to find the original, that's ok, but
   if searching for a selection of words in your issue title would have found
   the duplicate then the issue will likely be closed extremely abruptly.
2. When filing bug reports about exceptions or tracebacks, please include the
   *complete* traceback. Partial tracebacks, or just the exception text, are
   not helpful. Issues that do not contain complete tracebacks may be closed
   without warning.
3. Make sure you provide a suitable amount of information to work with. This
   means you should provide:

   - Guidance on **how to reproduce the issue**. Ideally, this should be a
     *small* code sample that can be run immediately by the maintainers.
     Failing that, let us know what you're doing, how often it happens, what
     environment you're using, etc. Be thorough: it prevents us needing to ask
     further questions.
   - Tell us **what you expected to happen**. When we run your example code,
     what are we expecting to happen? What does "success" look like for your
     code?
   - Tell us **what actually happens**. It's not helpful for you to say "it
     doesn't work" or "it fails". Tell us *how* it fails: do you get an
     exception? A None answer? How was the actual result
     different from your expected result?
   - Tell us **what version of Charset Normalizer you're using**, and
     **how you installed it**. Different versions of Charset Normalizer behave
     differently and have different bugs.

   If you do not provide all of these things, it will take us much longer to
   fix your problem. If we ask you to clarify these, and you never respond, we
   will close your issue without fixing it.


## What PR are we accepting?

Mostly anything, from cosmetic to the detection-mechanism improvement at the solo condition that you do not break
the backward-compatibility.

## What PR may be doomed?

  - Dropping EOL Python 3.5
> Scheduled for the 3.0 milestone.

  - Add support for a Python unsupported charset/encoding
> If you looked carefully at the project, you would see that it aims to be generic whenever possible. So adding a specific prober is out of the question.

  - Of course, if the CI/CD are failing
> Getting the discussion started often mean doing the minimum effort to get it Green! (Be reassured, maintainers will look into it, given a reasonable amount of time)

  - Submitting a PR without any description OR viable commit description
> This is obvious, maintainers need to understand as fast as possible what are you trying to submit without putting too much effort.

## How to run tests locally?

It is essential that you run, prior to any submissions the mandatory checks.
Run the script `./bin/run_checks.sh` to verify that your modification are not breaking anything.

Also, make sure to run the `./bin/run_autofix.sh` to comply with the style format and import sorting.
