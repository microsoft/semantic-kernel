---
name: Wrong charset / Detection issue
about: Create a report to help us improve the detection mechanism
title: "[DETECTION]"
labels: help wanted, detection
assignees: ''

---

**Notice**
I hereby announce that my raw input is not :
- Too small content (<=32 characters) as I do know that ANY charset detector heavily depends on content
- Encoded in a deprecated/abandoned encoding that is not even supported by my interpreter

**Provide the file**
A accessible way of retrieving the file concerned. Host it somewhere with untouched encoding.

**Verbose output**
Using the CLI, run `normalizer -v ./my-file.txt` and past the result in here.

```
(venv) >normalizer -v ./data/sample.1.ar.srt
2021-05-21 08:38:44,050 | DEBUG | ascii does not fit given bytes sequence at ALL. 'ascii' codec can't decode byte 0xca in position 54: ordinal not in range(128)
2021-05-21 08:38:44,051 | DEBUG | big5 does not fit given bytes sequence at ALL. 'big5' codec can't decode byte 0xc9 in position 60: illegal multibyte sequence
2021-05-21 08:38:44,051 | DEBUG | big5hkscs does not fit given bytes sequence at ALL. 'big5hkscs' codec can't decode byte 0xc9 in position 60: illegal multibyte sequence
....
```

**Expected encoding**
A clear and concise description of what you expected as encoding. Any more details about how the current guess is wrong
is very much appreciated.

**Desktop (please complete the following information):**
 - OS: [e.g. Linux, Windows or Mac]
 - Python version [e.g. 3.5]
 - Package version [eg. 2.0.0]

**Additional context**
Add any other context about the problem here.
