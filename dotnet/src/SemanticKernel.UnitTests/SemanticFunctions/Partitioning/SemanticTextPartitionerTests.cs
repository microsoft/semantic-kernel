// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.SemanticFunctions.Partitioning;
using Xunit;

namespace SemanticKernel.UnitTests.SemanticFunctions.Partitioning;

public sealed class SemanticTextPartitionerTests
{
    [Fact]
    public void CanSplitPlainTextLines()
    {
        const string input = "This is a test of the emergency broadcast system. This is only a test.";
        var expected = new[]
        {
            "This is a test of the emergency broadcast system.",
            "This is only a test."
        };

        var result = SemanticTextPartitioner.SplitPlainTextLines(input, 15);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void CanSplitMarkdownParagraphs()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system. This is only a test.",
            "We repeat, this is only a test. A unit test."
        };
        var expected = new[]
        {
            "This is a test of the emergency broadcast system.",
            "This is only a test.",
            "We repeat, this is only a test. A unit test."
        };

        var result = SemanticTextPartitioner.SplitMarkdownParagraphs(input, 13);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void CanSplitTextParagraphs()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system. This is only a test.",
            "We repeat, this is only a test. A unit test."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system.",
            "This is only a test.",
            "We repeat, this is only a test. A unit test."
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 13);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void CanSplitMarkDownLines()
    {
        const string input = "This is a test of the emergency broadcast system. This is only a test.";
        var expected = new[]
        {
            "This is a test of the emergency broadcast system.",
            "This is only a test."
        };

        var result = SemanticTextPartitioner.SplitMarkDownLines(input, 15);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void CanSplitTextParagraphsWithEmptyInput()
    {
        List<string> input = new();

        var expected = new List<string>();

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 13);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void CanSplitMarkdownParagraphsWithEmptyInput()
    {
        List<string> input = new();

        var expected = new List<string>();

        var result = SemanticTextPartitioner.SplitMarkdownParagraphs(input, 13);

        Assert.Equal(expected, result);
    }

    [Fact]
    public void CanSplitTextParagraphsEvenly()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system. This is only a test.",
            "We repeat, this is only a test. A unit test.",
            "A small note. And another. And once again. Seriously, this is the end. We're finished. All set. Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system.",
            "This is only a test.",
            "We repeat, this is only a test. A unit test.",
            "A small note. And another. And once again.",
            "Seriously, this is the end. We're finished. All set. Bye. Done."
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on \r or \n
    [Fact]
    public void CanSplitTextParagraphsOnNewlines()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system\r\nThis is only a test",
            "We repeat this is only a test\nA unit test",
            "A small note\nAnd another\r\nAnd once again\rSeriously this is the end\nWe're finished\nAll set\nBye\n",
            "Done"
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system",
            "This is only a test",
            "We repeat this is only a test\nA unit test",
            "A small note\nAnd another\nAnd once again",
            "Seriously this is the end\nWe're finished\nAll set\nBye Done",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on ? or !
    [Fact]
    public void CanSplitTextParagraphsOnPunctuation()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system. This is only a test",
            "We repeat, this is only a test? A unit test",
            "A small note! And another? And once again! Seriously, this is the end. We're finished. All set. Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system.",
            "This is only a test",
            "We repeat, this is only a test? A unit test",
            "A small note! And another? And once again!",
            "Seriously, this is the end.",
            $"We're finished. All set. Bye.{Environment.NewLine}Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on ;
    [Fact]
    public void CanSplitTextParagraphsOnSemicolons()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system; This is only a test",
            "We repeat; this is only a test; A unit test",
            "A small note; And another; And once again; Seriously, this is the end; We're finished; All set; Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system;",
            "This is only a test",
            "We repeat; this is only a test; A unit test",
            "A small note; And another; And once again;",
            "Seriously, this is the end; We're finished; All set; Bye. Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on :
    [Fact]
    public void CanSplitTextParagraphsOnColons()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system: This is only a test",
            "We repeat: this is only a test: A unit test",
            "A small note: And another: And once again: Seriously, this is the end: We're finished: All set: Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system:",
            "This is only a test",
            "We repeat: this is only a test: A unit test",
            "A small note: And another: And once again:",
            "Seriously, this is the end: We're finished: All set: Bye. Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on ,
    [Fact]
    public void CanSplitTextParagraphsOnCommas()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system, This is only a test",
            "We repeat, this is only a test, A unit test",
            "A small note, And another, And once again, Seriously, this is the end, We're finished, All set, Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system,",
            "This is only a test",
            "We repeat, this is only a test, A unit test",
            "A small note, And another, And once again, Seriously,",
            $"this is the end, We're finished, All set, Bye.{Environment.NewLine}Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on ) or ] or }
    [Fact]
    public void CanSplitTextParagraphsOnClosingBrackets()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system) This is only a test",
            "We repeat) this is only a test) A unit test",
            "A small note] And another) And once again] Seriously this is the end} We're finished} All set} Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency broadcast system)",
            "This is only a test",
            "We repeat) this is only a test) A unit test",
            "A small note] And another) And once again]",
            "Seriously this is the end} We're finished} All set} Bye. Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on ' '
    [Fact]
    public void CanSplitTextParagraphsOnSpaces()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system This is only a test",
            "We repeat this is only a test A unit test",
            "A small note And another And once again Seriously this is the end We're finished All set Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency",
            "broadcast system This is only a test",
            "We repeat this is only a test A unit test",
            "A small note And another And once again Seriously",
            $"this is the end We're finished All set Bye.{Environment.NewLine}Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that splits on '-'
    [Fact]
    public void CanSplitTextParagraphsOnHyphens()
    {
        List<string> input = new()
        {
            "This is a test of the emergency broadcast system-This is only a test",
            "We repeat-this is only a test-A unit test",
            "A small note-And another-And once again-Seriously, this is the end-We're finished-All set-Bye.",
            "Done."
        };

        var expected = new[]
        {
            "This is a test of the emergency",
            "broadcast system-This is only a test",
            "We repeat-this is only a test-A unit test",
            "A small note-And another-And once again-Seriously,",
            $"this is the end-We're finished-All set-Bye.{Environment.NewLine}Done.",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a plaintext example that does not have any of the above characters
    [Fact]
    public void CanSplitTextParagraphsWithNoDelimiters()
    {
        List<string> input = new()
        {
            "Thisisatestoftheemergencybroadcastsystem",
            "Thisisonlyatest",
            "WerepeatthisisonlyatestAunittest",
            "AsmallnoteAndanotherAndonceagain",
            "SeriouslythisistheendWe'refinishedAllsetByeDoneThisOneWillBeSplitToMeetTheLimit",
        };

        var expected = new[]
        {
            $"Thisisatestoftheemergencybroadcastsystem{Environment.NewLine}Thisisonlyatest",
            "WerepeatthisisonlyatestAunittest",
            "AsmallnoteAndanotherAndonceagain",
            "SeriouslythisistheendWe'refinishedAllse",
            "tByeDoneThisOneWillBeSplitToMeetTheLimit",
        };

        var result = SemanticTextPartitioner.SplitPlainTextParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a markdown example that splits on .

    // a markdown example that splits on ? or !

    // a markdown example that splits on ;

    // a markdown example that splits on :

    // a markdown example that splits on ,

    // a markdown example that splits on ) or ] or }

    // a markdown example that splits on ' '

    // a markdown example that splits on '-'

    // a markdown example that splits on '\r' or '\n'
    [Fact]
    public void CanSplitMarkdownParagraphsOnNewlines()
    {
        List<string> input = new()
        {
            "This_is_a_test_of_the_emergency_broadcast_system\r\nThis_is_only_a_test",
            "We_repeat_this_is_only_a_test\nA_unit_test",
            "A_small_note\nAnd_another\r\nAnd_once_again\rSeriously_this_is_the_end\nWe're_finished\nAll_set\nBye\n",
            "Done"
        };

        var expected = new[]
        {
            "This_is_a_test_of_the_emergency_broadcast_system",
            "This_is_only_a_test",
            "We_repeat_this_is_only_a_test\nA_unit_test",
            "A_small_note\nAnd_another\nAnd_once_again",
            "Seriously_this_is_the_end\nWe're_finished\nAll_set\nBye Done",
        };

        var result = SemanticTextPartitioner.SplitMarkdownParagraphs(input, 15);

        Assert.Equal(expected, result);
    }

    // a markdown example that does not have any of the above characters
}
