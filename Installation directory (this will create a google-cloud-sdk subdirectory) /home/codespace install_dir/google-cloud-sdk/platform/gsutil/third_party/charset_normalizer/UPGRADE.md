Guide to upgrade your code from v1 to v2
----------------------------------------

  * If you are using the legacy `detect` function, that is it. You have nothing to do.

## Detection

### Before

```python
from charset_normalizer import CharsetNormalizerMatches

results = CharsetNormalizerMatches.from_bytes(
    '我没有埋怨，磋砣的只是一些时间。'.encode('utf_32')
)
```

### After

```python
from charset_normalizer import from_bytes

results = from_bytes(
    '我没有埋怨，磋砣的只是一些时间。'.encode('utf_32')
)
```

Methods that once were staticmethods of the class `CharsetNormalizerMatches` are now basic functions.
`from_fp`, `from_bytes`, `from_fp` and `` are concerned.

Staticmethods scheduled to be removed in version 3.0
