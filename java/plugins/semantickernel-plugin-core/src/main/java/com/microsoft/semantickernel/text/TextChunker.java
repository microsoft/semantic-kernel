// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.text;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Split text in chunks, attempting to leave meaning intact. For plain text, split looking at new
 * lines first, then periods, and so on. For markdown, split looking at punctuation first, and so
 * on.
 */
public class TextChunker {
    private static final String s_spaceChar = " ";
    private static final List<Pattern> s_plaintextSplitOptions =
            Stream.of("[\n\r]", "\\.", "[\\?\\!]", ";", ":", ",", "[\\)\\]\\}]", " ", "\\-", null)
                    .map(it -> it == null ? null : Pattern.compile(it, Pattern.MULTILINE))
                    .collect(Collectors.toList());

    private static final List<Pattern> s_markdownSplitOptions =
            Stream.of("\\.", "[\\?\\!]", ";", ":", ",", "[\\)\\]\\}]", " ", "\\-", "[\n\r]", null)
                    .map(it -> it == null ? null : Pattern.compile(it, Pattern.MULTILINE))
                    .collect(Collectors.toList());

    /**
     * Split plain text into lines
     *
     * @param text Text to split
     * @param maxTokensPerLine Maximum number of tokens per line
     * @return List of lines
     */
    public static List<String> splitPlainTextLines(String text, int maxTokensPerLine) {
        return internalSplitLines(text, maxTokensPerLine, true, s_plaintextSplitOptions);
    }

    /**
     * Split markdown text into lines
     *
     * @param text Text to split
     * @param maxTokensPerLine Maximum number of tokens per line
     * @return List of lines
     */
    public static List<String> splitMarkDownLines(String text, int maxTokensPerLine) {
        List<String> result = new ArrayList<>();
        internalSplitLines(text, maxTokensPerLine, true, s_markdownSplitOptions);
        return result;
    }

    /**
     * Split plain text into paragraphs
     *
     * @param lines Lines of text
     * @param maxTokensPerParagraph Maximum number of tokens per paragraph.
     * @return List of paragraphs
     */
    public static List<String> splitPlainTextParagraphs(
            List<String> lines, int maxTokensPerParagraph) {
        return internalSplitTextParagraphs(
                lines,
                maxTokensPerParagraph,
                (text) ->
                        internalSplitLines(
                                text, maxTokensPerParagraph, false, s_plaintextSplitOptions));
    }

    /**
     * Split markdown text into paragraphs
     *
     * @param lines Lines of text
     * @param maxTokensPerParagraph Maximum number of tokens per paragraph
     * @return List of paragraphs
     */
    public static List<String> splitMarkdownParagraphs(
            List<String> lines, int maxTokensPerParagraph) {
        return internalSplitTextParagraphs(
                lines,
                maxTokensPerParagraph,
                (text) ->
                        internalSplitLines(
                                text, maxTokensPerParagraph, false, s_markdownSplitOptions));
    }

    private static List<String> internalSplitTextParagraphs(
            List<String> lines,
            int maxTokensPerParagraph,
            Function<String, List<String>> longLinesSplitter) {
        if (lines.size() == 0) {
            return new ArrayList<>();
        }

        // Split long lines first
        ArrayList<String> truncatedLines = new ArrayList<>();
        for (String line : lines) {
            truncatedLines.addAll(longLinesSplitter.apply(line));
        }

        lines = truncatedLines;

        // Group lines in paragraphs
        List<String> paragraphs = new ArrayList<>();
        StringBuilder currentParagraph = new StringBuilder();

        for (String line : lines) {
            // "+1" to account for the "new line" added by AppendLine()
            if (currentParagraph.length() > 0
                    && TokenCount(currentParagraph.length()) + TokenCount(line.length()) + 1
                            >= maxTokensPerParagraph) {
                paragraphs.add(currentParagraph.toString().trim());
                currentParagraph = new StringBuilder();
            }

            currentParagraph.append(line).append("\n");
        }

        if (currentParagraph.length() > 0) {
            paragraphs.add(currentParagraph.toString().trim());
        }

        // distribute text more evenly in the last paragraphs when the last paragraph is too short.
        if (paragraphs.size() > 1) {
            String lastParagraph = paragraphs.get(paragraphs.size() - 1);
            String secondLastParagraph = paragraphs.get(paragraphs.size() - 2);

            if (TokenCount(lastParagraph.length()) < maxTokensPerParagraph / 4) {
                List<String> lastParagraphTokens =
                        Arrays.stream(lastParagraph.split(s_spaceChar))
                                .filter(it -> it.length() != 0)
                                .collect(Collectors.toList());
                List<String> secondLastParagraphTokens =
                        Arrays.stream(secondLastParagraph.split(s_spaceChar))
                                .filter(it -> it.length() != 0)
                                .collect(Collectors.toList());

                int lastParagraphTokensCount = lastParagraphTokens.size();
                int secondLastParagraphTokensCount = secondLastParagraphTokens.size();

                if (lastParagraphTokensCount + secondLastParagraphTokensCount
                        <= maxTokensPerParagraph) {
                    StringBuilder newSecondLastParagraph = new StringBuilder();
                    for (int i = 0; i < secondLastParagraphTokensCount; i++) {
                        if (newSecondLastParagraph.length() != 0) {
                            newSecondLastParagraph.append(' ');
                        }

                        newSecondLastParagraph.append(secondLastParagraphTokens.get(i));
                    }

                    for (int i = 0; i < lastParagraphTokensCount; i++) {
                        if (newSecondLastParagraph.length() != 0) {
                            newSecondLastParagraph.append(' ');
                        }

                        newSecondLastParagraph.append(lastParagraphTokens.get(i));
                    }

                    paragraphs.set(paragraphs.size() - 2, newSecondLastParagraph.toString().trim());
                    paragraphs.remove(paragraphs.size() - 1);
                }
            }
        }

        return paragraphs;
    }

    private static class SplitString {
        public final boolean inputWasSplit;
        public final List<String> result;

        private SplitString(boolean inputWasSplit, List<String> result) {
            this.inputWasSplit = inputWasSplit;
            this.result = result;
        }
    }

    private static List<String> internalSplitLines(
            String text, int maxTokensPerLine, boolean trim, List<Pattern> splitOptions) {
        text = text.replaceAll("\\r?\\n|\\r", "\n");

        SplitString result =
                split(text, maxTokensPerLine, Collections.singletonList(splitOptions.get(0)), trim);
        if (result.inputWasSplit) {
            for (int i = 1; i < splitOptions.size(); i++) {
                result =
                        split(
                                result.result,
                                maxTokensPerLine,
                                Collections.singletonList(splitOptions.get(i)),
                                trim);

                if (!result.inputWasSplit) {
                    break;
                }
            }
        }
        return result.result;
    }

    private static SplitString split(
            List<String> input, int maxTokens, List<Pattern> separators, boolean trim) {
        List<String> result = new ArrayList<>();
        boolean modified = false;
        for (String str : input) {
            SplitString r = split(str, maxTokens, separators, trim);
            result.addAll(r.result);

            modified |= r.inputWasSplit;
        }
        return new SplitString(modified, result);
    }

    private static int indexOfAny(List<Pattern> separators, String input) {
        return separators.stream()
                .map(
                        it -> {
                            Matcher matcher = it.matcher(input);
                            if (matcher.find()) {
                                return matcher.start();
                            } else {
                                return -1;
                            }
                        })
                .filter(it -> it != -1)
                .min(Integer::compareTo)
                .orElse(-1);
    }

    private static SplitString split(
            String input, int maxTokens, List<Pattern> separators, boolean trim) {
        // Debug.Assert(inputString is null || input.SequenceEqual(inputString.AsSpan()));
        boolean inputWasSplit;
        if (TokenCount(input.length()) > maxTokens) {

            inputWasSplit = true;

            int half = input.length() / 2;
            int cutPoint = -1;

            if (separators.size() == 1 && separators.get(0) == null) {
                cutPoint = half;
            } else if (input.length() > 2) {
                int pos = 0;
                while (true) {
                    int index = indexOfAny(separators, input.substring(pos, input.length() - 1));
                    if (index < 0) {
                        break;
                    }

                    index += pos;

                    if (Math.abs(half - index) < Math.abs(half - cutPoint)) {
                        cutPoint = index + 1;
                    }

                    pos = index + 1;
                }
            }

            List<String> result = Collections.singletonList(input);

            if (cutPoint > 0) {
                String firstHalf = input.substring(0, cutPoint);
                String secondHalf = input.substring(cutPoint);
                if (trim) {
                    firstHalf = firstHalf.trim();
                    secondHalf = secondHalf.trim();
                }

                // Recursion
                SplitString first = split(firstHalf, maxTokens, separators, trim);
                SplitString second = split(secondHalf, maxTokens, separators, trim);

                result =
                        Stream.concat(first.result.stream(), second.result.stream())
                                .collect(Collectors.toList());
                inputWasSplit = first.inputWasSplit || second.inputWasSplit;
            }

            return new SplitString(inputWasSplit, result);
        }

        return new SplitString(false, Collections.singletonList(input));
    }

    private static int TokenCount(int inputLength) {
        // TODO: partitioning methods should be configurable to allow for different tokenization
        // strategies
        //       depending on the model to be called. For now, we use an extremely rough estimate.
        return inputLength / 4;
    }
}
