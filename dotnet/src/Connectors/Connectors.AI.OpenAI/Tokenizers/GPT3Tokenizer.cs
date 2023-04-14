// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
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
    private static readonly ConcurrentDictionary<string, string> s_bpeCache = new();

    private static ConcurrentDictionary<int, char>? s_bytesToUnicodeCache;

    // Regex for English contractions, e.g. "he's", "we'll", "I'm" etc.
    private static readonly Regex s_encodingRegex = new(
        @"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+", RegexOptions.Compiled,
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
        if (string.IsNullOrEmpty(text)) { return new List<int>(); }

        ConcurrentDictionary<int, char> byteEncoder = BytesToUnicode();
        IReadOnlyCollection<Match> matches = (IReadOnlyCollection<Match>)s_encodingRegex.Matches(text);

        var bpeTokens = new List<int>();
        foreach (var match in matches)
        {
            var token = new string(Encoding.UTF8.GetBytes(match.Value).Select(x => byteEncoder[x]).ToArray());
            List<int> newTokens = BytePairEncoding(token).Split(' ').Select(x => GPT3Settings.Encoder[x]).ToList();
            bpeTokens.AddRange(newTokens);
        }

        return bpeTokens;
    }

    public static List<int> Encode(StringBuilder? stringBuilder)
    {
        return stringBuilder == null ? new List<int>() : Encode(stringBuilder.ToString());
    }

    public static List<int> Encode(char[]? chars)
    {
        return chars == null ? new List<int>() : Encode(new string(chars));
    }

    public static List<int> Encode(IEnumerable<char>? chars)
    {
        return chars == null ? new List<int>() : Encode(chars.ToArray());
    }

    private static int Ord(string x) => char.ConvertToUtf32(x, 0);

    private static ConcurrentDictionary<int, char> BytesToUnicode()
    {
        // Note: no visible gain with this
        if (s_bytesToUnicodeCache != null) { return s_bytesToUnicodeCache; }

        List<int> bytes = Enumerable.Range(Ord("!"), Ord("~") + 1 - Ord("!"))
            .Concat(Enumerable.Range(Ord("¡"), Ord("¬") + 1 - Ord("¡")))
            .Concat(Enumerable.Range(Ord("®"), Ord("ÿ") + 1 - Ord("®")))
            .ToList();

        List<char> chars = (from x in bytes select (char)x).ToList();

        int n = 0;
        for (int b = 0; b < 256; b++)
        {
            if (bytes.Contains(b)) { continue; }

            bytes.Add(b);
            chars.Add((char)(256 + n++));
        }

        s_bytesToUnicodeCache = new ConcurrentDictionary<int, char>(bytes
            .Zip(chars, (k, v) => new { k, v })
            .ToDictionary(x => x.k, x => x.v));

        return s_bytesToUnicodeCache;
    }

    private static string BytePairEncoding(string token)
    {
        if (s_bpeCache.TryGetValue(token, out string value))
        {
            return value;
        }

        List<string> word = (from x in token.ToList() select x.ToString()).ToList();
        List<Tuple<string, string>> pairs = GetPairs(word);
        if (pairs.Count == 0)
        {
            s_bpeCache.TryAdd(token, token);
            return token;
        }

        while (true)
        {
            var minPairs = new SortedDictionary<long, Tuple<string, string>>();
            foreach (Tuple<string, string> pair in pairs)
            {
                if (GPT3Settings.BpeRanks.TryGetValue(pair, out _))
                {
                    int rank = GPT3Settings.BpeRanks[pair];
                    minPairs[rank] = pair;
                }
                else
                {
                    minPairs[100000000000] = pair;
                }
            }

            Tuple<string, string> biGram = minPairs[minPairs.Keys.Min()];
            if (!GPT3Settings.BpeRanks.ContainsKey(biGram)) { break; }

            string first = biGram.Item1;
            string second = biGram.Item2;

            var newWord = new List<string>();
            int i = 0;

            while (i < word.Count)
            {
                int j = word.IndexOf(first, i);

                if (j == -1)
                {
                    var slice = new ArraySegment<string>((from x in word select x.ToString()).ToArray(), i, word.Count - i);
                    newWord.AddRange(slice);
                    break;
                }

                var slice2 = new ArraySegment<string>((from x in word select x.ToString()).ToArray(), i, j - i);
                newWord.AddRange(slice2);
                i = j;

                if (word[i] == first && i < (word.Count - 1) && word[i + 1] == second)
                {
                    newWord.Add($"{first}{second}");
                    i += 2;
                }
                else
                {
                    newWord.Add(word[i]);
                    i += 1;
                }
            }

            word = newWord;
            if (word.Count == 1) { break; }

            pairs = GetPairs(word);
        }

        string result = string.Join(" ", word);
        s_bpeCache.TryAdd(token, result);
        return result;
    }

    /// <summary>
    /// Return set of symbol pairs in a word.
    /// </summary>
    private static List<Tuple<string, string>> GetPairs(List<string> word)
    {
        var result = new List<Tuple<string, string>>();

        string prevChar = word[0];
        for (int i = 1; i < word.Count; i++)
        {
            string currentChar = word[i];
            result.Add(new Tuple<string, string>(prevChar, currentChar));
            prevChar = currentChar;
        }

        return result;
    }
}
