// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Split text in chunks, attempting to leave meaning intact.
/// For plain text, split looking at new lines first, then periods, and so on.
/// For markdown, split looking at punctuation first, and so on.
/// </summary>
[Experimental("SKEXP0050")]
public static class TextChunker
{
    /// <summary>
    /// Represents a list of strings with token count.
    /// Used to reduce the number of calls to the tokenizer.
    /// </summary>
    private sealed class StringListWithTokenCount(TextChunker.TokenCounter? tokenCounter)
    {
        private readonly TokenCounter? _tokenCounter = tokenCounter;

        public void Add(string value) => this.Values.Add((value, this._tokenCounter is null ? GetDefaultTokenCount(value.Length) : this._tokenCounter(value)));

        public void Add(string value, int tokenCount) => this.Values.Add((value, tokenCount));

        public void AddRange(StringListWithTokenCount range) => this.Values.AddRange(range.Values);

        public void RemoveRange(int index, int count) => this.Values.RemoveRange(index, count);

        public int Count => this.Values.Count;

        public List<string> ToStringList() => this.Values.Select(v => v.Value).ToList();

        private List<(string Value, int TokenCount)> Values { get; } = [];

        public string ValueAt(int i) => this.Values[i].Value;

        public int TokenCountAt(int i) => this.Values[i].TokenCount;
    }

    /// <summary>
    /// Delegate for counting tokens in a string.
    /// </summary>
    /// <param name="input">The input string to count tokens in.</param>
    /// <returns>The number of tokens in the input string.</returns>
    public delegate int TokenCounter(string input);

    private static readonly char[] s_spaceChar = [' '];
    private static readonly string?[] s_plaintextSplitOptions = ["\n", ".。．", "?!", ";", ":", ",，、", ")]}", " ", "-", null];
    private static readonly string?[] s_markdownSplitOptions = [".\u3002\uFF0E", "?!", ";", ":", ",\uFF0C\u3001", ")]}", " ", "-", "\n\r", null];

    /// <summary>
    /// Split plain text into lines.
    /// </summary>
    /// <param name="text">Text to split</param>
    /// <param name="maxTokensPerLine">Maximum number of tokens per line.</param>
    /// <param name="tokenCounter">Function to count tokens in a string. If not supplied, the default counter will be used.</param>
    /// <returns>List of lines.</returns>
    public static List<string> SplitPlainTextLines(string text, int maxTokensPerLine, TokenCounter? tokenCounter = null) =>
        InternalSplitLines(text, maxTokensPerLine, trim: true, s_plaintextSplitOptions, tokenCounter);

    /// <summary>
    /// Split markdown text into lines.
    /// </summary>
    /// <param name="text">Text to split</param>
    /// <param name="maxTokensPerLine">Maximum number of tokens per line.</param>
    /// <param name="tokenCounter">Function to count tokens in a string. If not supplied, the default counter will be used.</param>
    /// <returns>List of lines.</returns>
    public static List<string> SplitMarkDownLines(string text, int maxTokensPerLine, TokenCounter? tokenCounter = null) =>
        InternalSplitLines(text, maxTokensPerLine, trim: true, s_markdownSplitOptions, tokenCounter);

    /// <summary>
    /// Split plain text into paragraphs.
    /// </summary>
    /// <param name="lines">Lines of text.</param>
    /// <param name="maxTokensPerParagraph">Maximum number of tokens per paragraph.</param>
    /// <param name="overlapTokens">Number of tokens to overlap between paragraphs.</param>
    /// <param name="chunkHeader">Text to be prepended to each individual chunk.</param>
    /// <param name="tokenCounter">Function to count tokens in a string. If not supplied, the default counter will be used.</param>
    /// <returns>List of paragraphs.</returns>
    public static List<string> SplitPlainTextParagraphs(
    IEnumerable<string> lines,
    int maxTokensPerParagraph,
    int overlapTokens = 0,
    string? chunkHeader = null,
    TokenCounter? tokenCounter = null) =>
    InternalSplitTextParagraphs(
        lines.Select(line => line
            .Replace("\r\n", "\n")
            .Replace('\r', '\n')),
        maxTokensPerParagraph,
        overlapTokens,
        chunkHeader,
        static (text, maxTokens, tokenCounter) => InternalSplitLines(text, maxTokens, trim: false, s_plaintextSplitOptions, tokenCounter),
        tokenCounter);

    /// <summary>
    /// Split markdown text into paragraphs.
    /// </summary>
    /// <param name="lines">Lines of text.</param>
    /// <param name="maxTokensPerParagraph">Maximum number of tokens per paragraph.</param>
    /// <param name="overlapTokens">Number of tokens to overlap between paragraphs.</param>
    /// <param name="chunkHeader">Text to be prepended to each individual chunk.</param>
    /// <param name="tokenCounter">Function to count tokens in a string. If not supplied, the default counter will be used.</param>
    /// <returns>List of paragraphs.</returns>
    public static List<string> SplitMarkdownParagraphs(IEnumerable<string> lines, int maxTokensPerParagraph, int overlapTokens = 0, string? chunkHeader = null, TokenCounter? tokenCounter = null) =>
        InternalSplitTextParagraphs(lines, maxTokensPerParagraph, overlapTokens, chunkHeader, static (text, maxTokens, tokenCounter) => InternalSplitLines(text, maxTokens, trim: false, s_markdownSplitOptions, tokenCounter), tokenCounter);

    private static List<string> InternalSplitTextParagraphs(IEnumerable<string> lines, int maxTokensPerParagraph, int overlapTokens, string? chunkHeader, Func<string, int, TokenCounter?, List<string>> longLinesSplitter, TokenCounter? tokenCounter)
    {
        if (maxTokensPerParagraph <= 0)
        {
            throw new ArgumentException("maxTokensPerParagraph should be a positive number", nameof(maxTokensPerParagraph));
        }

        if (maxTokensPerParagraph <= overlapTokens)
        {
            throw new ArgumentException("overlapTokens cannot be larger than maxTokensPerParagraph", nameof(maxTokensPerParagraph));
        }

        // Optimize empty inputs if we can efficiently determine the're empty
        if (lines is ICollection<string> c && c.Count == 0)
        {
            return [];
        }

        var chunkHeaderTokens = chunkHeader is { Length: > 0 } ? GetTokenCount(chunkHeader, tokenCounter) : 0;
        var adjustedMaxTokensPerParagraph = maxTokensPerParagraph - overlapTokens - chunkHeaderTokens;

        // Split long lines first
        IEnumerable<string> truncatedLines = lines.SelectMany(line => longLinesSplitter(line, adjustedMaxTokensPerParagraph, tokenCounter));

        var paragraphs = BuildParagraph(truncatedLines, adjustedMaxTokensPerParagraph, tokenCounter);
        var processedParagraphs = ProcessParagraphs(paragraphs, adjustedMaxTokensPerParagraph, overlapTokens, chunkHeader, longLinesSplitter, tokenCounter);

        return processedParagraphs;
    }

    private static List<string> BuildParagraph(IEnumerable<string> truncatedLines, int maxTokensPerParagraph, TokenCounter? tokenCounter)
    {
        StringBuilder paragraphBuilder = new();
        List<string> paragraphs = [];

        foreach (string line in truncatedLines)
        {
            if (paragraphBuilder.Length > 0)
            {
                string? paragraph = null;

                int currentCount = GetTokenCount(line, tokenCounter) + 1;
                if (currentCount < maxTokensPerParagraph)
                {
                    currentCount += tokenCounter is null ?
                        GetDefaultTokenCount(paragraphBuilder.Length) :
                        tokenCounter(paragraph = paragraphBuilder.ToString());
                }

                if (currentCount >= maxTokensPerParagraph)
                {
                    // Complete the paragraph and prepare for the next
                    paragraph ??= paragraphBuilder.ToString();
                    paragraphs.Add(paragraph.Trim());
                    paragraphBuilder.Clear();
                }
            }

            paragraphBuilder.AppendLine(line);
        }

        if (paragraphBuilder.Length > 0)
        {
            // Add the final paragraph if there's anything remaining
            paragraphs.Add(paragraphBuilder.ToString().Trim());
        }

        return paragraphs;
    }

    private static List<string> ProcessParagraphs(List<string> paragraphs, int adjustedMaxTokensPerParagraph, int overlapTokens, string? chunkHeader, Func<string, int, TokenCounter?, List<string>> longLinesSplitter, TokenCounter? tokenCounter)
    {
        // distribute text more evenly in the last paragraphs when the last paragraph is too short.
        if (paragraphs.Count > 1)
        {
            var lastParagraph = paragraphs[paragraphs.Count - 1];
            var secondLastParagraph = paragraphs[paragraphs.Count - 2];

            if (GetTokenCount(lastParagraph, tokenCounter) < adjustedMaxTokensPerParagraph / 4)
            {
                var lastParagraphTokens = lastParagraph.Split(s_spaceChar, StringSplitOptions.RemoveEmptyEntries);
                var secondLastParagraphTokens = secondLastParagraph.Split(s_spaceChar, StringSplitOptions.RemoveEmptyEntries);

                var lastParagraphTokensCount = lastParagraphTokens.Length;
                var secondLastParagraphTokensCount = secondLastParagraphTokens.Length;

                if (lastParagraphTokensCount + secondLastParagraphTokensCount <= adjustedMaxTokensPerParagraph)
                {
                    var newSecondLastParagraph = string.Join(" ", secondLastParagraphTokens);
                    var newLastParagraph = string.Join(" ", lastParagraphTokens);

                    paragraphs[paragraphs.Count - 2] = $"{newSecondLastParagraph} {newLastParagraph}";
                    paragraphs.RemoveAt(paragraphs.Count - 1);
                }
            }
        }

        var processedParagraphs = new List<string>();
        var paragraphStringBuilder = new StringBuilder();

        for (int i = 0; i < paragraphs.Count; i++)
        {
            paragraphStringBuilder.Clear();

            if (chunkHeader is not null)
            {
                paragraphStringBuilder.Append(chunkHeader);
            }

            var paragraph = paragraphs[i];

            if (overlapTokens > 0 && i < paragraphs.Count - 1)
            {
                var nextParagraph = paragraphs[i + 1];
                var split = longLinesSplitter(nextParagraph, overlapTokens, tokenCounter);

                paragraphStringBuilder.Append(paragraph);

                if (split.Count != 0)
                {
                    paragraphStringBuilder.Append(' ').Append(split[0]);
                }
            }
            else
            {
                paragraphStringBuilder.Append(paragraph);
            }

            processedParagraphs.Add(paragraphStringBuilder.ToString());
        }

        return processedParagraphs;
    }

    private static List<string> InternalSplitLines(string text, int maxTokensPerLine, bool trim, string?[] splitOptions, TokenCounter? tokenCounter)
    {
        var result = new StringListWithTokenCount(tokenCounter);

        text = text.Replace("\r\n", "\n"); // normalize line endings
        result.Add(text);
        for (int i = 0; i < splitOptions.Length; i++)
        {
            int count = result.Count; // track where the original input left off
            var (splits2, inputWasSplit2) = Split(result, maxTokensPerLine, splitOptions[i].AsSpan(), trim, tokenCounter);
            result.AddRange(splits2);
            result.RemoveRange(0, count); // remove the original input
            if (!inputWasSplit2)
            {
                break;
            }
        }
        return result.ToStringList();
    }

    private static (StringListWithTokenCount, bool) Split(StringListWithTokenCount input, int maxTokens, ReadOnlySpan<char> separators, bool trim, TokenCounter? tokenCounter)
    {
        bool inputWasSplit = false;
        StringListWithTokenCount result = new(tokenCounter);
        int count = input.Count;
        for (int i = 0; i < count; i++)
        {
            var (splits, split) = Split(input.ValueAt(i).AsSpan(), input.ValueAt(i), maxTokens, separators, trim, tokenCounter, input.TokenCountAt(i));
            result.AddRange(splits);
            inputWasSplit |= split;
        }
        return (result, inputWasSplit);
    }

    private static (StringListWithTokenCount, bool) Split(ReadOnlySpan<char> input, string? inputString, int maxTokens, ReadOnlySpan<char> separators, bool trim, TokenCounter? tokenCounter, int inputTokenCount)
    {
        Debug.Assert(inputString is null || input.SequenceEqual(inputString.AsSpan()));
        StringListWithTokenCount result = new(tokenCounter);
        var inputWasSplit = false;

        if (inputTokenCount > maxTokens)
        {
            inputWasSplit = true;

            int half = input.Length / 2;
            int cutPoint = -1;

            if (separators.IsEmpty)
            {
                cutPoint = half;
            }
            else if (input.Length > 2)
            {
                int pos = 0;
                while (true)
                {
                    int index = input.Slice(pos, input.Length - 1 - pos).IndexOfAny(separators);
                    if (index < 0)
                    {
                        break;
                    }

                    index += pos;

                    if (Math.Abs(half - index) < Math.Abs(half - cutPoint))
                    {
                        cutPoint = index + 1;
                    }

                    pos = index + 1;
                }
            }

            if (cutPoint > 0)
            {
                var firstHalf = input.Slice(0, cutPoint);
                var secondHalf = input.Slice(cutPoint);
                if (trim)
                {
                    firstHalf = firstHalf.Trim();
                    secondHalf = secondHalf.Trim();
                }

                // Recursion
                var (splits1, split1) = Split(firstHalf, null, maxTokens, separators, trim, tokenCounter, GetTokenCount(firstHalf.ToString(), tokenCounter));
                result.AddRange(splits1);
                var (splits2, split2) = Split(secondHalf, null, maxTokens, separators, trim, tokenCounter, GetTokenCount(secondHalf.ToString(), tokenCounter));
                result.AddRange(splits2);

                inputWasSplit = split1 || split2;
                return (result, inputWasSplit);
            }
        }

        var resultString = inputString ?? input.ToString();
        var resultTokenCount = inputTokenCount;
        if (trim && !resultString.Trim().Equals(resultString, StringComparison.Ordinal))
        {
            resultString = resultString.Trim();
            resultTokenCount = GetTokenCount(resultString, tokenCounter);
        }

        result.Add(resultString, resultTokenCount);

        return (result, inputWasSplit);
    }

    private static int GetTokenCount(string input, TokenCounter? tokenCounter) => tokenCounter is null ? GetDefaultTokenCount(input.Length) : tokenCounter(input);

    private static int GetDefaultTokenCount(int length)
    {
        Debug.Assert(length >= 0);
        return length >> 2;
    }
}
