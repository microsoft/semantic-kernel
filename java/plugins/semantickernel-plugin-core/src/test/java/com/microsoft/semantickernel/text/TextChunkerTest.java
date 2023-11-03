// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.text;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class TextChunkerTest {

    @Test
    public void canSplitPlainTextLines() {
        String input = "This is a test of the emergency broadcast system. This is only a test.";
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system.",
                        "This is only a test.");

        List<String> result = TextChunker.splitPlainTextLines(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitPlainTextLinesWithComma() {
        String input = "This is a test, of the emergency broadcast system. This is only a test.";
        List<String> expected =
                Arrays.asList(
                        "This is a test,",
                        "of the emergency broadcast system.",
                        "This is only a test.");

        List<String> result = TextChunker.splitPlainTextLines(input, 10);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitPlainTextLinesLongString() {
        String input =
                "This is a very very very very very very long string with nothing to split on.";
        List<String> expected =
                Arrays.asList(
                        "This is a very very very very very very",
                        "long string with nothing to split on.");

        List<String> result = TextChunker.splitPlainTextLines(input, 10);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitPlainTextLinesLongStringWithSmallTokenCount() {
        String input =
                "This is a very very very very very very very very very very very long string.";
        List<String> expected =
                Arrays.asList(
                        "This is a",
                        "very very",
                        "very very",
                        "very very",
                        "very very",
                        "very very",
                        "very long",
                        "string.");

        List<String> result = TextChunker.splitPlainTextLines(input, 2);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitPlainTextLinesNoSeparator() {
        String input = "Thisisaveryveryveryveryveryverylongstringwithnothingtospliton";
        List<String> expected =
                Arrays.asList("Thisisaveryveryveryveryveryver", "ylongstringwithnothingtospliton");

        List<String> result = TextChunker.splitPlainTextLines(input, 10);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitMarkdownParagraphs() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system. This is only a test.",
                        "We repeat, this is only a test. A unit test.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system.",
                        "This is only a test.",
                        "We repeat, this is only a test. A unit test.");

        List<String> result = TextChunker.splitMarkdownParagraphs(input, 13);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphs() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system. This is only a test.",
                        "We repeat, this is only a test. A unit test.");

        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system.",
                        "This is only a test.",
                        "We repeat, this is only a test. A unit test.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 13);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitMarkdownParagraphsWithEmptyInput() {
        List<String> input = Collections.emptyList();

        List<String> expected = Collections.emptyList();

        List<String> result = TextChunker.splitMarkdownParagraphs(input, 13);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsEvenly() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system. This is only a test.",
                        "We repeat, this is only a test. A unit test.",
                        "A small note. And another. And once again. Seriously, this is the end."
                                + " We're finished. All set. Bye.",
                        "Done.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system.",
                        "This is only a test.",
                        "We repeat, this is only a test. A unit test.",
                        "A small note. And another. And once again.",
                        "Seriously, this is the end. We're finished. All set. Bye. Done.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnNewlines() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system\r\nThis is only a test",
                        "We repeat this is only a test\nA unit test",
                        "A small note\n"
                                + "And another\r\n"
                                + "And once again\r"
                                + "Seriously this is the end\n"
                                + "We're finished\n"
                                + "All set\n"
                                + "Bye\n",
                        "Done");

        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system",
                        "This is only a test",
                        "We repeat this is only a test\nA unit test",
                        "A small note\nAnd another\nAnd once again",
                        "Seriously this is the end\nWe're finished\nAll set\nBye Done");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnPunctuation() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system. This is only a test",
                        "We repeat, this is only a test? A unit test",
                        "A small note! And another? And once again! Seriously, this is the end."
                                + " We're finished. All set. Bye.",
                        "Done.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system.",
                        "This is only a test",
                        "We repeat, this is only a test? A unit test",
                        "A small note! And another? And once again!",
                        "Seriously, this is the end.",
                        "We're finished. All set. Bye.\nDone.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnSemicolons() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system; This is only a test",
                        "We repeat; this is only a test; A unit test",
                        "A small note; And another; And once again; Seriously, this is the end;"
                                + " We're finished; All set; Bye.",
                        "Done.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system;",
                        "This is only a test",
                        "We repeat; this is only a test; A unit test",
                        "A small note; And another; And once again;",
                        "Seriously, this is the end; We're finished; All set; Bye. Done.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnColons() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system: This is only a test",
                        "We repeat: this is only a test: A unit test",
                        "A small note: And another: And once again: Seriously, this is the end:"
                                + " We're finished: All set: Bye.",
                        "Done.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system:",
                        "This is only a test",
                        "We repeat: this is only a test: A unit test",
                        "A small note: And another: And once again:",
                        "Seriously, this is the end: We're finished: All set: Bye. Done.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnCommas() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system, This is only a test",
                        "We repeat, this is only a test, A unit test",
                        "A small note, And another, And once again, Seriously, this is the end,"
                                + " We're finished, All set, Bye.",
                        "Done.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system,",
                        "This is only a test",
                        "We repeat, this is only a test, A unit test",
                        "A small note, And another, And once again, Seriously,",
                        "this is the end, We're finished, All set, Bye." + "\n" + "Done.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnClosingBrackets() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system) This is only a test",
                        "We repeat) this is only a test) A unit test",
                        "A small note] And another) And once again] Seriously this is the end}"
                                + " We're finished} All set} Bye.",
                        "Done.");

        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency broadcast system)",
                        "This is only a test",
                        "We repeat) this is only a test) A unit test",
                        "A small note] And another) And once again]",
                        "Seriously this is the end} We're finished} All set} Bye. Done.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsOnHyphens() {
        List<String> input =
                Arrays.asList(
                        "This is a test of the emergency broadcast system-This is only a test",
                        "We repeat-this is only a test-A unit test",
                        "A small note-And another-And once again-Seriously, this is the end-We're"
                                + " finished-All set-Bye.",
                        "Done.");
        List<String> expected =
                Arrays.asList(
                        "This is a test of the emergency",
                        "broadcast system-This is only a test",
                        "We repeat-this is only a test-A unit test",
                        "A small note-And another-And once again-Seriously,",
                        "this is the end-We're finished-All set-Bye." + "\n" + "Done.");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitTextParagraphsWithNoDelimiters() {
        List<String> input =
                Arrays.asList(
                        "Thisisatestoftheemergencybroadcastsystem",
                        "Thisisonlyatest",
                        "WerepeatthisisonlyatestAunittest",
                        "AsmallnoteAndanotherAndonceagain",
                        "SeriouslythisistheendWe'refinishedAllsetByeDoneThisOneWillBeSplitToMeetTheLimit");
        List<String> expected =
                Arrays.asList(
                        "Thisisatestoftheemergencybroadcastsystem" + "\n" + "Thisisonlyatest",
                        "WerepeatthisisonlyatestAunittest",
                        "AsmallnoteAndanotherAndonceagain",
                        "SeriouslythisistheendWe'refinishedAllse",
                        "tByeDoneThisOneWillBeSplitToMeetTheLimit");

        List<String> result = TextChunker.splitPlainTextParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }

    @Test
    public void canSplitMarkdownParagraphsOnNewlines() {
        List<String> input =
                Arrays.asList(
                        "This_is_a_test_of_the_emergency_broadcast_system\r\nThis_is_only_a_test",
                        "We_repeat_this_is_only_a_test\nA_unit_test",
                        "A_small_note\n"
                                + "And_another\r\n"
                                + "And_once_again\r"
                                + "Seriously_this_is_the_end\n"
                                + "We're_finished\n"
                                + "All_set\n"
                                + "Bye\n",
                        "Done");

        List<String> expected =
                Arrays.asList(
                        "This_is_a_test_of_the_emergency_broadcast_system",
                        "This_is_only_a_test",
                        "We_repeat_this_is_only_a_test\nA_unit_test",
                        "A_small_note\nAnd_another\nAnd_once_again",
                        "Seriously_this_is_the_end\nWe're_finished\nAll_set\nBye Done");

        List<String> result = TextChunker.splitMarkdownParagraphs(input, 15);

        Assertions.assertEquals(expected, result);
    }
}
