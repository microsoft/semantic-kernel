Frequently asked questions
==========================

What is character encoding?
---------------------------

When you think of “text”, you probably think of “characters and symbols
I see on my computer screen”. But computers don’t deal in characters and
symbols; they deal in bits and bytes. Every piece of text you’ve ever
seen on a computer screen is actually stored in a particular *character
encoding*. There are many different character encodings, some optimized
for particular languages like Russian or Chinese or English, and others
that can be used for multiple languages. Very roughly speaking, the
character encoding provides a mapping between the stuff you see on your
screen and the stuff your computer actually stores in memory and on
disk.

In reality, it’s more complicated than that. Many characters are common
to multiple encodings, but each encoding may use a different sequence of
bytes to actually store those characters in memory or on disk. So you
can think of the character encoding as a kind of decryption key for the
text. Whenever someone gives you a sequence of bytes and claims it’s
“text”, you need to know what character encoding they used so you can
decode the bytes into characters and display them (or process them, or
whatever).

What is character encoding auto-detection?
------------------------------------------

It means taking a sequence of bytes in an unknown character encoding,
and attempting to determine the encoding so you can read the text. It’s
like cracking a code when you don’t have the decryption key.

Isn’t that impossible?
----------------------

In general, yes. However, some encodings are optimized for specific
languages, and languages are not random. Some character sequences pop up
all the time, while other sequences make no sense. A person fluent in
English who opens a newspaper and finds “txzqJv 2!dasd0a QqdKjvz” will
instantly recognize that that isn’t English (even though it is composed
entirely of English letters). By studying lots of “typical” text, a
computer algorithm can simulate this kind of fluency and make an
educated guess about a text’s language.

In other words, encoding detection is really language detection,
combined with knowledge of which languages tend to use which character
encodings.

Who wrote this detection algorithm?
-----------------------------------

This library is a port of `the auto-detection code in
Mozilla <http://lxr.mozilla.org/seamonkey/source/extensions/universalchardet/src/base/>`__.
I have attempted to maintain as much of the original structure as
possible (mostly for selfish reasons, to make it easier to maintain the
port as the original code evolves). I have also retained the original
authors’ comments, which are quite extensive and informative.

You may also be interested in the research paper which led to the
Mozilla implementation, `A composite approach to language/encoding
detection <http://www-archive.mozilla.org/projects/intl/UniversalCharsetDetection.html>`__.

Yippie! Screw the standards, I’ll just auto-detect everything!
--------------------------------------------------------------

Don’t do that. Virtually every format and protocol contains a method for
specifying character encoding.

-  HTTP can define a ``charset`` parameter in the ``Content-type``
   header.
-  HTML documents can define a ``<meta http-equiv="content-type">``
   element in the ``<head>`` of a web page.
-  XML documents can define an ``encoding`` attribute in the XML prolog.

If text comes with explicit character encoding information, you should
use it. If the text has no explicit information, but the relevant
standard defines a default encoding, you should use that. (This is
harder than it sounds, because standards can overlap. If you fetch an
XML document over HTTP, you need to support both standards *and* figure
out which one wins if they give you conflicting information.)

Despite the complexity, it’s worthwhile to follow standards and `respect
explicit character encoding
information <http://www.w3.org/2001/tag/doc/mime-respect>`__. It will
almost certainly be faster and more accurate than trying to auto-detect
the encoding. It will also make the world a better place, since your
program will interoperate with other programs that follow the same
standards.

Why bother with auto-detection if it’s slow, inaccurate, and non-standard?
--------------------------------------------------------------------------

Sometimes you receive text with verifiably inaccurate encoding
information. Or text without any encoding information, and the specified
default encoding doesn’t work. There are also some poorly designed
standards that have no way to specify encoding at all.

If following the relevant standards gets you nowhere, *and* you decide
that processing the text is more important than maintaining
interoperability, then you can try to auto-detect the character encoding
as a last resort. An example is my `Universal Feed
Parser <https://pythonhosted.org/feedparser/>`__, which calls this auto-detection
library `only after exhausting all other
options <https://pythonhosted.org/feedparser/character-encoding.html>`__.
