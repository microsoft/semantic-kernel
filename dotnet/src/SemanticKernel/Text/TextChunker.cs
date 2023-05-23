// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Split text in chunks, attempting to leave meaning intact.
/// For plain text, split looking at new lines first, then periods, and so on.
/// For markdown, split looking at punctuation first, and so on.
/// </summary>
public static class TextChunker
{
    private static readonly char[] s_spaceChar = new[] { ' ' };
    private static readonly string?[] s_plaintextSplitOptions = new[] { "\n\r", ".", "?!", ";", ":", ",", ")]}", " ", "-", null };
    private static readonly string?[] s_markdownSplitOptions = new[] { ".", "?!", ";", ":", ",", ")]}", " ", "-", "\n\r", null };

    /// <summary>
    /// Split plain text into lines.
    /// </summary>
    /// <param name="text">Text to split</param>
    /// <param name="maxTokensPerLine">Maximum number of tokens per line.</param>
    /// <returns>List of lines.</returns>
    public static List<string> SplitPlainTextLines(string text, int maxTokensPerLine)
    {
        return InternalSplitLines(text, maxTokensPerLine, trim: true, s_plaintextSplitOptions);
    }

    /// <summary>
    /// Split markdown text into lines.
    /// </summary>
    /// <param name="text">Text to split</param>
    /// <param name="maxTokensPerLine">Maximum number of tokens per line.</param>
    /// <returns>List of lines.</returns>
    public static List<string> SplitMarkDownLines(string text, int maxTokensPerLine)
    {
        return InternalSplitLines(text, maxTokensPerLine, trim: true, s_markdownSplitOptions);
    }

    /// <summary>
    /// Split plain text into paragraphs.
    /// </summary>
    /// <param name="lines">Lines of text.</param>
    /// <param name="maxTokensPerParagraph">Maximum number of tokens per paragraph.</param>
    /// <returns>List of paragraphs.</returns>
    public static List<string> SplitPlainTextParagraphs(List<string> lines, int maxTokensPerParagraph)
    {
        return InternalSplitTextParagraphs(lines, maxTokensPerParagraph, text => InternalSplitLines(text, maxTokensPerParagraph, trim: false, s_plaintextSplitOptions));
    }

    /// <summary>
    /// Split markdown text into paragraphs.
    /// </summary>
    /// <param name="lines">Lines of text.</param>
    /// <param name="maxTokensPerParagraph">Maximum number of tokens per paragraph.</param>
    /// <returns>List of paragraphs.</returns>
    public static List<string> SplitMarkdownParagraphs(List<string> lines, int maxTokensPerParagraph)
    {
        return InternalSplitTextParagraphs(lines, maxTokensPerParagraph, text => InternalSplitLines(text, maxTokensPerParagraph, trim: false, s_markdownSplitOptions));
    }

    private static List<string> InternalSplitTextParagraphs(List<string> lines, int maxTokensPerParagraph, Func<string, List<string>> longLinesSplitter)
    {
        if (lines.Count == 0)
        {
            return new List<string>();
        }

        // Split long lines first
        var truncatedLines = lines.SelectMany(longLinesSplitter);

        // Group lines in paragraphs
          var paragraphs = truncatedLines.Aggregate(new { Paragraph = new StringBuilder(), Paragraphs = new List<string>() },
           (state, line) =>
           {
               if (state.Paragraph.Length > 0 &&
                   TokenCount(state.Paragraph.Length) + TokenCount(line.Length) + 1 >= maxTokensPerParagraph)
               {
                   state.Paragraphs.Add(state.Paragraph.ToString().Trim());
                   state.Paragraph.Clear();
               }

               state.Paragraph.AppendLine(line);

               return state;
           },
            finalState =>
            {
                if (finalState.Paragraph.Length > 0)
                {
                    finalState.Paragraphs.Add(finalState.Paragraph.ToString().Trim());
                }

                return finalState.Paragraphs;
            }
        );

        // distribute text more evenly in the last paragraphs when the last paragraph is too short.
        if (paragraphs.Count > 1)
        {
            var lastParagraph = paragraphs[paragraphs.Count - 1];
            var secondLastParagraph = paragraphs[paragraphs.Count - 2];

            if (TokenCount(lastParagraph.Length) < maxTokensPerParagraph / 4)
            {
                var lastParagraphTokens = lastParagraph.Split(s_spaceChar, StringSplitOptions.RemoveEmptyEntries);
                var secondLastParagraphTokens = secondLastParagraph.Split(s_spaceChar, StringSplitOptions.RemoveEmptyEntries);

                var lastParagraphTokensCount = lastParagraphTokens.Length;
                var secondLastParagraphTokensCount = secondLastParagraphTokens.Length;

                if (lastParagraphTokensCount + secondLastParagraphTokensCount <= maxTokensPerParagraph)
                {
                    var newSecondLastParagraph = string.Join(" ", secondLastParagraphTokens);
                    var newLastParagraph = string.Join(" ", lastParagraphTokens);

                    paragraphs[paragraphs.Count - 2] = $"{newSecondLastParagraph} {newLastParagraph}" ;
                    paragraphs.RemoveAt(paragraphs.Count - 1);
                }
            }
        }

        return paragraphs;
    }

    private static List<string> InternalSplitLines(string text, int maxTokensPerLine, bool trim, string?[] splitOptions)
    {
        var result = new List<string>();
        text = text.NormalizeLineEndings();
        result.Add(text);
        for (int i = 0; i < splitOptions.Length; i++)
        {
            int count = result.Count; // track where the original input left off
            var (splits2, inputWasSplit2) = Split(result, maxTokensPerLine, splitOptions[i].AsSpan(), trim);
            result.AddRange(splits2);
            result.RemoveRange(0, count); // remove the original input
            if (!inputWasSplit2)
            {
                break;
            }
        }
        return result;
    }

    private static (List<string>, bool) Split(List<string> input, int maxTokens, ReadOnlySpan<char> separators, bool trim)
    {
        bool inputWasSplit = false;
        List<string> result = new List<string>();
        int count = input.Count;
        for (int i = 0; i < count; i++)
        {
            var (splits, split) = Split(input[i].AsSpan(), input[i], maxTokens, separators, trim);
            result.AddRange(splits);
            inputWasSplit |= split;
        }
        return (result, inputWasSplit);
    }

    private static (List<string>,bool) Split(ReadOnlySpan<char> input, string? inputString, int maxTokens, ReadOnlySpan<char> separators, bool trim)
    {
        Debug.Assert(inputString is null || input.SequenceEqual(inputString.AsSpan()));
        List<string> result = new List<string>();
        var inputWasSplit = false;
        if (TokenCount(input.Length) > maxTokens)
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
                var (splits1, split1) = Split(firstHalf, null, maxTokens, separators, trim);
                result.AddRange(splits1);
                var (splits2, split2) = Split(secondHalf, null, maxTokens, separators, trim);
                result.AddRange(splits2) ;

                inputWasSplit = split1 || split2;
                return (result, inputWasSplit);
            }
        }

        result.Add((inputString is not null, trim) switch
        {
            (true, true) => inputString!.Trim(),
            (true, false) => inputString!,
            (false, true) => input.Trim().ToString(),
            (false, false) => input.ToString(),
        });

        return (result, inputWasSplit);
    }

    private static int TokenCount(int inputLength)
    {
        // TODO: partitioning methods should be configurable to allow for different tokenization strategies
        //       depending on the model to be called. For now, we use an extremely rough estimate.
        return inputLength / 4;
    }
}
