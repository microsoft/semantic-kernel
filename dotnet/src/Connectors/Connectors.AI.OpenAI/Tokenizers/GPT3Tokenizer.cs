// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Buffers;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers.Settings;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers;

/// <summary>
/// Port of GPT3 Javascript tokenizer recommended by OpenAI.
/// See https://platform.openai.com/tokenizer and
/// https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
/// </summary>
public static class GPT3Tokenizer
{
    private static readonly ConcurrentDictionary<string, List<string>> s_bpeCache = new();

    /// <summary>Lookup table from byte (index) to associated char.</summary>
    /// <remarks>Computed result of function at https://github.com/openai/gpt-2/blob/a74da5d99abaaba920de8131d64da2862a8f213b/src/encoder.py#L9-L28.</remarks>
    private static readonly char[] s_bytesToUnicode = new char[]
    {
        (char)0x0100, (char)0x0101, (char)0x0102, (char)0x0103, (char)0x0104, (char)0x0105, (char)0x0106, (char)0x0107,
        (char)0x0108, (char)0x0109, (char)0x010A, (char)0x010B, (char)0x010C, (char)0x010D, (char)0x010E, (char)0x010F,
        (char)0x0110, (char)0x0111, (char)0x0112, (char)0x0113, (char)0x0114, (char)0x0115, (char)0x0116, (char)0x0117,
        (char)0x0118, (char)0x0119, (char)0x011A, (char)0x011B, (char)0x011C, (char)0x011D, (char)0x011E, (char)0x011F,
        (char)0x0120, (char)0x0021, (char)0x0022, (char)0x0023, (char)0x0024, (char)0x0025, (char)0x0026, (char)0x0027,
        (char)0x0028, (char)0x0029, (char)0x002A, (char)0x002B, (char)0x002C, (char)0x002D, (char)0x002E, (char)0x002F,
        (char)0x0030, (char)0x0031, (char)0x0032, (char)0x0033, (char)0x0034, (char)0x0035, (char)0x0036, (char)0x0037,
        (char)0x0038, (char)0x0039, (char)0x003A, (char)0x003B, (char)0x003C, (char)0x003D, (char)0x003E, (char)0x003F,
        (char)0x0040, (char)0x0041, (char)0x0042, (char)0x0043, (char)0x0044, (char)0x0045, (char)0x0046, (char)0x0047,
        (char)0x0048, (char)0x0049, (char)0x004A, (char)0x004B, (char)0x004C, (char)0x004D, (char)0x004E, (char)0x004F,
        (char)0x0050, (char)0x0051, (char)0x0052, (char)0x0053, (char)0x0054, (char)0x0055, (char)0x0056, (char)0x0057,
        (char)0x0058, (char)0x0059, (char)0x005A, (char)0x005B, (char)0x005C, (char)0x005D, (char)0x005E, (char)0x005F,
        (char)0x0060, (char)0x0061, (char)0x0062, (char)0x0063, (char)0x0064, (char)0x0065, (char)0x0066, (char)0x0067,
        (char)0x0068, (char)0x0069, (char)0x006A, (char)0x006B, (char)0x006C, (char)0x006D, (char)0x006E, (char)0x006F,
        (char)0x0070, (char)0x0071, (char)0x0072, (char)0x0073, (char)0x0074, (char)0x0075, (char)0x0076, (char)0x0077,
        (char)0x0078, (char)0x0079, (char)0x007A, (char)0x007B, (char)0x007C, (char)0x007D, (char)0x007E, (char)0x0121,
        (char)0x0122, (char)0x0123, (char)0x0124, (char)0x0125, (char)0x0126, (char)0x0127, (char)0x0128, (char)0x0129,
        (char)0x012A, (char)0x012B, (char)0x012C, (char)0x012D, (char)0x012E, (char)0x012F, (char)0x0130, (char)0x0131,
        (char)0x0132, (char)0x0133, (char)0x0134, (char)0x0135, (char)0x0136, (char)0x0137, (char)0x0138, (char)0x0139,
        (char)0x013A, (char)0x013B, (char)0x013C, (char)0x013D, (char)0x013E, (char)0x013F, (char)0x0140, (char)0x0141,
        (char)0x0142, (char)0x00A1, (char)0x00A2, (char)0x00A3, (char)0x00A4, (char)0x00A5, (char)0x00A6, (char)0x00A7,
        (char)0x00A8, (char)0x00A9, (char)0x00AA, (char)0x00AB, (char)0x00AC, (char)0x0143, (char)0x00AE, (char)0x00AF,
        (char)0x00B0, (char)0x00B1, (char)0x00B2, (char)0x00B3, (char)0x00B4, (char)0x00B5, (char)0x00B6, (char)0x00B7,
        (char)0x00B8, (char)0x00B9, (char)0x00BA, (char)0x00BB, (char)0x00BC, (char)0x00BD, (char)0x00BE, (char)0x00BF,
        (char)0x00C0, (char)0x00C1, (char)0x00C2, (char)0x00C3, (char)0x00C4, (char)0x00C5, (char)0x00C6, (char)0x00C7,
        (char)0x00C8, (char)0x00C9, (char)0x00CA, (char)0x00CB, (char)0x00CC, (char)0x00CD, (char)0x00CE, (char)0x00CF,
        (char)0x00D0, (char)0x00D1, (char)0x00D2, (char)0x00D3, (char)0x00D4, (char)0x00D5, (char)0x00D6, (char)0x00D7,
        (char)0x00D8, (char)0x00D9, (char)0x00DA, (char)0x00DB, (char)0x00DC, (char)0x00DD, (char)0x00DE, (char)0x00DF,
        (char)0x00E0, (char)0x00E1, (char)0x00E2, (char)0x00E3, (char)0x00E4, (char)0x00E5, (char)0x00E6, (char)0x00E7,
        (char)0x00E8, (char)0x00E9, (char)0x00EA, (char)0x00EB, (char)0x00EC, (char)0x00ED, (char)0x00EE, (char)0x00EF,
        (char)0x00F0, (char)0x00F1, (char)0x00F2, (char)0x00F3, (char)0x00F4, (char)0x00F5, (char)0x00F6, (char)0x00F7,
        (char)0x00F8, (char)0x00F9, (char)0x00FA, (char)0x00FB, (char)0x00FC, (char)0x00FD, (char)0x00FE, (char)0x00FF
    };

    /// <summary>
    /// Regex for English contractions, e.g. "he's", "we'll", "I'm" etc.
    /// </summary>
    private static readonly Regex s_encodingRegex = new(
        @"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+",
        RegexOptions.Compiled,
        TimeSpan.FromSeconds(5));

    /// <summary>
    /// The tokenizer uses a byte-pair encoding (BPE) algorithm to split words into
    /// sub-words based on frequency and merges rules. It can handle out-of-vocabulary
    /// words, punctuation, and special tokens.
    /// </summary>
    /// <param name="text">Text to tokenize</param>
    /// <returns>List of token IDs</returns>
    public static List<int> Encode(string text)
    {
        var bpeTokens = new List<int>();

        if (!string.IsNullOrEmpty(text))
        {
            // Find all the matches.
            MatchCollection matches = s_encodingRegex.Matches(text);

            // Determine the maximum number of UTF8 bytes that any match value could require.
            int maxUtf8Length = 0;
            for (int i = 0; i < matches.Count; i++)
            {
                Match m = matches[i];
                int utf8Length = EncodingUtf8GetByteCount(text.AsSpan(m.Index, m.Length));
                if (utf8Length > maxUtf8Length)
                {
                    maxUtf8Length = utf8Length;
                }
            }

            // Ensure we have a sufficient Span<char> buffer to accommodate maxUtf8Length chars.
            // The byte-to-char mapping scheme employed is 1:1, so we'll end up needing 1 char
            // for every 1 UTF8 byte. If we can reasonably stack-allocate the space, we do, otherwise
            // we temporarily rent a pooled array.
            char[]? arrayPoolArray = null;
            Span<char> chars = maxUtf8Length <= 256
                ? stackalloc char[maxUtf8Length]
                : (arrayPoolArray = ArrayPool<char>.Shared.Rent(maxUtf8Length));

            // Rather than using separate space for the UTF8 bytes, we just reinterpret the Span<char>
            // as a Span<byte>.  Since our mapping is 1:1, the space required for the bytes will always
            // be half of the space required for the chars.  We can UTF8-encode into the first half, and
            // then walk backwards through the bytes, using the byte-to-char mapping scheme to populate
            // the chars from the back to the front. By going in reverse, we guarantee we won't overwrite
            // any bytes we haven't yet seen.
            Span<byte> bytes = MemoryMarshal.AsBytes(chars);

            // Now that our space is created, do the actual encoding.
            for (int matchIndex = 0; matchIndex < matches.Count; matchIndex++)
            {
                // Get the matched text as a span.
                Match m = matches[matchIndex];
                ReadOnlySpan<char> matchValue = text.AsSpan(m.Index, m.Length);

                // Encode the UTF8 bytes.
                int bytesWritten = EncodingUtf8GetBytes(matchValue, bytes);

                // Translate those bytes into chars.
                char[] bytesToUnicode = s_bytesToUnicode;
                for (int i = bytesWritten - 1; i >= 0; i--)
                {
                    chars[i] = bytesToUnicode[bytes[i]];
                }

                // Evaluate the BPE for the encoded chars.
                foreach (string encoding in BytePairEncoding(chars.Slice(0, bytesWritten).ToString()))
                {
                    bpeTokens.Add(GPT3Settings.Encoder[encoding]);
                }
            }

            // Return the rented array to the pool if we rented one.
            if (arrayPoolArray is not null)
            {
                ArrayPool<char>.Shared.Return(arrayPoolArray);
            }
        }

        return bpeTokens;

        static unsafe int EncodingUtf8GetByteCount(ReadOnlySpan<char> chars)
        {
            fixed (char* charsPtr = chars)
            {
                return Encoding.UTF8.GetByteCount(charsPtr, chars.Length);
            }
        }

        static unsafe int EncodingUtf8GetBytes(ReadOnlySpan<char> chars, Span<byte> bytes)
        {
            fixed (char* charPtr = chars)
            {
                fixed (byte* bytesPtr = bytes)
                {
                    return Encoding.UTF8.GetBytes(charPtr, chars.Length, bytesPtr, bytes.Length);
                }
            }
        }
    }

    /// <summary>
    /// Tokenizes the text in the provided StringBuilder.
    /// </summary>
    /// <param name="stringBuilder">StringBuilder containing the text to tokenize</param>
    /// <returns>List of token IDs</returns>
    public static List<int> Encode(StringBuilder? stringBuilder) =>
        stringBuilder is not null
            ? Encode(stringBuilder.ToString())
            : new List<int>();

    /// <summary>
    /// Tokenizes the text in the provided char array.
    /// </summary>
    /// <param name="chars">Char array containing the text to tokenize</param>
    /// <returns>List of token IDs</returns>
    public static List<int> Encode(char[]? chars) =>
        chars is not null
            ? Encode(new string(chars))
            : new List<int>();

    /// <summary>
    /// Tokenizes the text in the provided IEnumerable of chars.
    /// </summary>
    /// <param name="chars">IEnumerable of chars containing the text to tokenize</param>
    /// <returns>List of token IDs</returns>
    public static List<int> Encode(IEnumerable<char>? chars) =>
        chars is not null
            ? Encode(string.Concat(chars))
            : new List<int>();

    private static List<string> BytePairEncoding(string token)
    {
        if (s_bpeCache.TryGetValue(token, out List<string>? value))
        {
            return value;
        }

        if (token.Length <= 1)
        {
            var list = new List<string>(1) { token };
            s_bpeCache.TryAdd(token, list);
            return list;
        }

        List<string> word = new(token.Length);
        foreach (char c in token)
        {
            word.Add(c.ToString());
        }

        long smallestRank = long.MaxValue;
        (string, string) smallestPair = ("", "");
        List<string>? newWord = null;

        while (word.Count >= 2)
        {
            for (int pairIndex = 0; pairIndex < word.Count - 1; pairIndex++)
            {
                (string, string) pair = (word[pairIndex], word[pairIndex + 1]);

                long pairRank = GPT3Settings.BpeRanks.TryGetValue(pair, out int rank) ? rank : 100_000_000_000;

                if (pairRank <= smallestRank)
                {
                    smallestRank = pairRank;
                    smallestPair = pair;
                }
            }

            if (!GPT3Settings.BpeRanks.ContainsKey(smallestPair))
            {
                break;
            }

            string first = smallestPair.Item1;
            string second = smallestPair.Item2;

            newWord ??= new List<string>(word.Count);
            for (int i = 0; i < word.Count; i++)
            {
                int j = word.IndexOf(first, i);

                int limit = j < 0 ? word.Count : j;
                for (int copy = i; copy < limit; copy++)
                {
                    newWord.Add(word[copy]);
                }

                if (j < 0)
                {
                    break;
                }

                i = j;

                if (i < (word.Count - 1) &&
                    word[i] == first &&
                    word[i + 1] == second)
                {
                    newWord.Add($"{first}{second}");
                    i++;
                }
                else
                {
                    newWord.Add(word[i]);
                }
            }

            // Swap the new word in for the old
            (word, newWord) = (newWord, word);

            // And reset state for the next go-around
            newWord.Clear();
            smallestRank = long.MaxValue;
        }

        s_bpeCache.TryAdd(token, word);
        return word;
    }
}
