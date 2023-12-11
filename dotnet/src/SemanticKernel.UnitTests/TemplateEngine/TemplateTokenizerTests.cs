// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine;

public class TemplateTokenizerTests
{
    private readonly TemplateTokenizer _target;

    public TemplateTokenizerTests()
    {
        this._target = new TemplateTokenizer();
    }

    [Theory]
    [InlineData(null, BlockTypes.Text)]
    [InlineData("", BlockTypes.Text)]
    [InlineData(" ", BlockTypes.Text)]
    [InlineData("   ", BlockTypes.Text)]
    [InlineData(" {}  ", BlockTypes.Text)]
    [InlineData(" {{}  ", BlockTypes.Text)]
    [InlineData(" {{ } } }  ", BlockTypes.Text)]
    [InlineData(" { { }} }", BlockTypes.Text)]
    [InlineData("{{}}", BlockTypes.Text)]
    [InlineData("{{ }}", BlockTypes.Text)]
    [InlineData("{{  }}", BlockTypes.Text)]
    [InlineData("{{  '}}x", BlockTypes.Text)]
    [InlineData("{{  \"}}x", BlockTypes.Text)]
    internal void ItParsesTextWithoutCode(string? text, BlockTypes type)
    {
        // Act
        var blocks = this._target.Tokenize(text);

        // Assert
        Assert.Single(blocks);
        Assert.Equal(type, blocks[0].Type);
    }

    [Theory]
    [InlineData("", BlockTypes.Text)]
    [InlineData(" ", BlockTypes.Text)]
    [InlineData("   ", BlockTypes.Text)]
    [InlineData(" aaa  ", BlockTypes.Text)]
    [InlineData("{{$}}", BlockTypes.Variable)]
    [InlineData("{{$a}}", BlockTypes.Variable)]
    [InlineData("{{ $a}}", BlockTypes.Variable)]
    [InlineData("{{ $a }}", BlockTypes.Variable)]
    [InlineData("{{  $a  }}", BlockTypes.Variable)]
    [InlineData("{{code}}", BlockTypes.Code)]
    [InlineData("{{code }}", BlockTypes.Code)]
    [InlineData("{{ code }}", BlockTypes.Code)]
    [InlineData("{{  code }}", BlockTypes.Code)]
    [InlineData("{{  code  }}", BlockTypes.Code)]
    [InlineData("{{''}}", BlockTypes.Value)]
    [InlineData("{{' '}}", BlockTypes.Value)]
    [InlineData("{{ ' '}}", BlockTypes.Value)]
    [InlineData("{{ ' ' }}", BlockTypes.Value)]
    [InlineData("{{  ' ' }}", BlockTypes.Value)]
    [InlineData("{{  ' '  }}", BlockTypes.Value)]
    internal void ItParsesBasicBlocks(string? text, BlockTypes type)
    {
        // Act
        var blocks = this._target.Tokenize(text);

        // Assert
        Assert.Single(blocks);
        Assert.Equal(type, blocks[0].Type);
    }

    [Theory]
    [InlineData(null, 1)]
    [InlineData("", 1)]
    [InlineData("}}{{a}} {{b}}x", 5)]
    [InlineData("}}{{ -a}} {{b}}x", 5)]
    [InlineData("}}{{ -a\n}} {{b}}x", 5)]
    [InlineData("}}{{ -a\n} } {{b}}x", 3)]
    public void ItTokenizesTheRightTokenCount(string? template, int blockCount)
    {
        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(blockCount, blocks.Count);
    }

    [Fact]
    public void ItTokenizesEdgeCasesCorrectly1()
    {
        // Act
        var blocks1 = this._target.Tokenize("{{{{a}}");
        var blocks2 = this._target.Tokenize("{{'{{a}}");
        var blocks3 = this._target.Tokenize("{{'a}}");
        var blocks4 = this._target.Tokenize("{{a'}}");

        // Assert - Count
        Assert.Equal(2, blocks1.Count);
        Assert.Single(blocks2);
        Assert.Single(blocks3);
        Assert.Single(blocks4);

        // Assert - Type
        Assert.Equal(BlockTypes.Text, blocks1[0].Type);
        Assert.Equal(BlockTypes.Code, blocks1[1].Type);

        // Assert - Content
        Assert.Equal("{{", blocks1[0].Content);
        Assert.Equal("a", blocks1[1].Content);
    }

    [Fact]
    public void ItTokenizesEdgeCasesCorrectly2()
    {
        // Arrange
        var template = "}}{{{ {$a}}}} {{b}}x}}";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(5, blocks.Count);

        Assert.Equal("}}{", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("{$a", blocks[1].Content);
        Assert.Equal(BlockTypes.Code, blocks[1].Type);

        Assert.Equal("}} ", blocks[2].Content);
        Assert.Equal(BlockTypes.Text, blocks[2].Type);

        Assert.Equal("b", blocks[3].Content);
        Assert.Equal(BlockTypes.Code, blocks[3].Type);

        Assert.Equal("x}}", blocks[4].Content);
        Assert.Equal(BlockTypes.Text, blocks[4].Type);
    }

    [Fact]
    public void ItTokenizesEdgeCasesCorrectly3()
    {
        // Arrange
        var template = "}}{{{{$a}}}} {{b}}$x}}";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(5, blocks.Count);

        Assert.Equal("}}{{", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("$a", blocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);

        Assert.Equal("}} ", blocks[2].Content);
        Assert.Equal(BlockTypes.Text, blocks[2].Type);

        Assert.Equal("b", blocks[3].Content);
        Assert.Equal(BlockTypes.Code, blocks[3].Type);

        Assert.Equal("$x}}", blocks[4].Content);
        Assert.Equal(BlockTypes.Text, blocks[4].Type);
    }

    [Theory]
    [InlineData("{{a$}}")]
    [InlineData("{{a$a}}")]
    [InlineData("{{a''}}")]
    [InlineData("{{a\"\"}}")]
    [InlineData("{{a'b'}}")]
    [InlineData("{{a\"b\"}}")]
    [InlineData("{{a'b'   }}")]
    [InlineData("{{a\"b\"    }}")]
    [InlineData("{{ asis 'f\\'oo' }}")]
    public void ItTokenizesEdgeCasesCorrectly4(string template)
    {
        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Single(blocks);
        Assert.Equal(BlockTypes.Code, blocks[0].Type);
        Assert.Equal(template.Substring(2, template.Length - 4).Trim(), blocks[0].Content);
    }

    [Fact]
    public void ItTokenizesATypicalPrompt()
    {
        // Arrange
        var template = "this is a {{ $prompt }} with {{$some}} variables " +
                       "and {{function $calls}} {{ and 'values' }}";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(8, blocks.Count);

        Assert.Equal("this is a ", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("$prompt", blocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);

        Assert.Equal(" with ", blocks[2].Content);
        Assert.Equal(BlockTypes.Text, blocks[2].Type);

        Assert.Equal("$some", blocks[3].Content);
        Assert.Equal(BlockTypes.Variable, blocks[3].Type);

        Assert.Equal(" variables and ", blocks[4].Content);
        Assert.Equal(BlockTypes.Text, blocks[4].Type);

        Assert.Equal("function $calls", blocks[5].Content);
        Assert.Equal(BlockTypes.Code, blocks[5].Type);

        Assert.Equal(" ", blocks[6].Content);
        Assert.Equal(BlockTypes.Text, blocks[6].Type);

        Assert.Equal("and 'values'", blocks[7].Content);
        Assert.Equal(BlockTypes.Code, blocks[7].Type);
    }

    [Fact]
    public void ItTokenizesAFunctionCallWithMultipleArguments()
    {
        // Arrange
        var template = "this is a {{ function with='many' named=$arguments }}";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(2, blocks.Count);

        Assert.Equal("this is a ", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("function with='many' named=$arguments", blocks[1].Content);
        Assert.Equal(BlockTypes.Code, blocks[1].Type);
    }

    [Fact]
    public void ItThrowsWhenCodeBlockStartsWithNamedArg()
    {
        // Arrange
        var template = "{{ not='valid' }}";

        // Assert
        var ex = Assert.Throws<KernelException>(() =>
        {
            // Act
            this._target.Tokenize(template);
        });
        Assert.Equal("Code tokenizer returned an incorrect first token type NamedArg", ex.Message);
    }

    [Fact]
    public void ItRendersVariables1()
    {
        // Arrange
        var template = "{$x11} This {$a} is {$_a} a {{$x11}} test {{$x11}} " +
                       "template {{foo}}{{bar $a}}{{baz $_a}}{{yay $x11}}{{food a='b' c = $d}}{{positional 'abc' p1=$p1}}";

        // Act
        var blocks = this._target.Tokenize(template);

        var renderedBlocks = RenderBlocks(blocks);

        // Assert
        Assert.Equal(11, blocks.Count);
        Assert.Equal(11, renderedBlocks.Count);

        Assert.Equal("$x11", blocks[1].Content);
        Assert.Equal("", renderedBlocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);
        Assert.Equal(BlockTypes.Text, renderedBlocks[1].Type);

        Assert.Equal("$x11", blocks[3].Content);
        Assert.Equal("", renderedBlocks[3].Content);
        Assert.Equal(BlockTypes.Variable, blocks[3].Type);
        Assert.Equal(BlockTypes.Text, renderedBlocks[3].Type);

        Assert.Equal("foo", blocks[5].Content);
        Assert.Equal("foo", renderedBlocks[5].Content);
        Assert.Equal(BlockTypes.Code, blocks[5].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[5].Type);

        Assert.Equal("bar $a", blocks[6].Content);
        Assert.Equal("bar $a", renderedBlocks[6].Content);
        Assert.Equal(BlockTypes.Code, blocks[6].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[6].Type);

        Assert.Equal("baz $_a", blocks[7].Content);
        Assert.Equal("baz $_a", renderedBlocks[7].Content);
        Assert.Equal(BlockTypes.Code, blocks[7].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[7].Type);

        Assert.Equal("yay $x11", blocks[8].Content);
        Assert.Equal("yay $x11", renderedBlocks[8].Content);
        Assert.Equal(BlockTypes.Code, blocks[8].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[8].Type);

        Assert.Equal("food a='b' c = $d", blocks[9].Content);
        Assert.Equal("food a='b' c = $d", renderedBlocks[9].Content);
        Assert.Equal(BlockTypes.Code, blocks[9].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[9].Type);

        // Arrange
        var arguments = new KernelArguments
        {
            ["x11"] = "x11 value",
            ["a"] = "a value",
            ["_a"] = "_a value",
            ["c"] = "c value",
            ["d"] = "d value",
            ["p1"] = "p1 value",
        };

        // Act
        blocks = this._target.Tokenize(template);
        renderedBlocks = RenderBlocks(blocks, arguments);

        // Assert
        Assert.Equal(11, blocks.Count);
        Assert.Equal(11, renderedBlocks.Count);

        Assert.Equal("$x11", blocks[1].Content);
        Assert.Equal("x11 value", renderedBlocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);
        Assert.Equal(BlockTypes.Text, renderedBlocks[1].Type);

        Assert.Equal("$x11", blocks[3].Content);
        Assert.Equal("x11 value", renderedBlocks[3].Content);
        Assert.Equal(BlockTypes.Variable, blocks[3].Type);
        Assert.Equal(BlockTypes.Text, renderedBlocks[3].Type);

        Assert.Equal("foo", blocks[5].Content);
        Assert.Equal("foo", renderedBlocks[5].Content);
        Assert.Equal(BlockTypes.Code, blocks[5].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[5].Type);

        Assert.Equal("bar $a", blocks[6].Content);
        Assert.Equal("bar $a", renderedBlocks[6].Content);
        Assert.Equal(BlockTypes.Code, blocks[6].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[6].Type);

        Assert.Equal("baz $_a", blocks[7].Content);
        Assert.Equal("baz $_a", renderedBlocks[7].Content);
        Assert.Equal(BlockTypes.Code, blocks[7].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[7].Type);

        Assert.Equal("yay $x11", blocks[8].Content);
        Assert.Equal("yay $x11", renderedBlocks[8].Content);
        Assert.Equal(BlockTypes.Code, blocks[8].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[8].Type);

        Assert.Equal("food a='b' c = $d", blocks[9].Content);
        Assert.Equal("food a='b' c = $d", renderedBlocks[9].Content);
        Assert.Equal(BlockTypes.Code, blocks[9].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[9].Type);

        Assert.Equal("positional 'abc' p1=$p1", blocks[10].Content);
        Assert.Equal("positional 'abc' p1=$p1", renderedBlocks[10].Content);
        Assert.Equal(BlockTypes.Code, blocks[10].Type);
        Assert.Equal(BlockTypes.Code, renderedBlocks[10].Type);
    }

    private static List<Block> RenderBlocks(IList<Block> blocks, KernelArguments? arguments = null)
    {
        return blocks.Select(block => block.Type != BlockTypes.Variable
            ? block
            : new TextBlock((string?)((ITextRendering)block).Render(arguments))).ToList();
    }
}
