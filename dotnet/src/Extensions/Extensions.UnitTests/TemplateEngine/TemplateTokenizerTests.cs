// Copyright (c) Microsoft. All rights reserved.

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
        Assert.Equal(1, blocks.Count);
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
        Assert.Equal(1, blocks.Count);
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
        Assert.Equal(1, blocks2.Count);
        Assert.Equal(1, blocks3.Count);
        Assert.Equal(1, blocks4.Count);

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
        Assert.Equal(1, blocks.Count);
        Assert.Equal(BlockTypes.Code, blocks[0].Type);
        Assert.Equal(template[2..^2].Trim(), blocks[0].Content);
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
}
