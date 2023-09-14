// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Prompt;
using Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Prompt;

public class CodeTokenizerTests
{
    private readonly CodeTokenizer _target;

    public CodeTokenizerTests()
    {
        this._target = new CodeTokenizer();
    }

    [Fact]
    public void ItParsesEmptyText()
    {
        // Act +  Assert
        Assert.Empty(this._target.Tokenize(null));
        Assert.Empty(this._target.Tokenize(""));
        Assert.Empty(this._target.Tokenize(" "));
        Assert.Empty(this._target.Tokenize(" \n "));
    }

    [Theory]
    [InlineData("$", "$")]
    [InlineData(" $ ", "$")]
    [InlineData("$foo", "$foo")]
    [InlineData("$foo ", "$foo")]
    [InlineData(" $foo", "$foo")]
    [InlineData(" $bar ", "$bar")]
    public void ItParsesVarBlocks(string template, string content)
    {
        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Single(blocks);
        Assert.Equal(content, blocks[0].Content);
        Assert.Equal(BlockTypes.Variable, blocks[0].Type);
    }

    [Theory]
    [InlineData("'", "'")]
    [InlineData(" \" ", "\"")]
    [InlineData("'foo'", "'foo'")]
    [InlineData("'foo' ", "'foo'")]
    [InlineData(" 'foo'", "'foo'")]
    [InlineData(" \"bar\" ", "\"bar\"")]
    public void ItParsesValBlocks(string template, string content)
    {
        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Single(blocks);
        Assert.Equal(content, blocks[0].Content);
        Assert.Equal(BlockTypes.Value, blocks[0].Type);
    }

    [Theory]
    [InlineData("f", "f")]
    [InlineData(" x ", "x")]
    [InlineData("foo", "foo")]
    [InlineData("fo.o ", "fo.o")]
    [InlineData(" f.oo", "f.oo")]
    [InlineData(" bar ", "bar")]
    public void ItParsesFunctionIdBlocks(string template, string content)
    {
        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Single(blocks);
        Assert.Equal(content, blocks[0].Content);
        Assert.Equal(BlockTypes.FunctionId, blocks[0].Type);
    }

    [Fact]
    public void ItParsesFunctionCalls()
    {
        // Arrange
        var template1 = "x.y $foo";
        var template2 = "xy $foo";
        var template3 = "xy '$value'";

        // Act
        var blocks1 = this._target.Tokenize(template1);
        var blocks2 = this._target.Tokenize(template2);
        var blocks3 = this._target.Tokenize(template3);

        // Assert
        Assert.Equal(2, blocks1.Count);
        Assert.Equal(2, blocks2.Count);
        Assert.Equal(2, blocks3.Count);

        Assert.Equal("x.y", blocks1[0].Content);
        Assert.Equal("xy", blocks2[0].Content);
        Assert.Equal("xy", blocks3[0].Content);

        Assert.Equal(BlockTypes.FunctionId, blocks1[0].Type);
        Assert.Equal(BlockTypes.FunctionId, blocks2[0].Type);
        Assert.Equal(BlockTypes.FunctionId, blocks3[0].Type);

        Assert.Equal("$foo", blocks1[1].Content);
        Assert.Equal("$foo", blocks2[1].Content);
        Assert.Equal("'$value'", blocks3[1].Content);

        Assert.Equal(BlockTypes.Variable, blocks1[1].Type);
        Assert.Equal(BlockTypes.Variable, blocks2[1].Type);
        Assert.Equal(BlockTypes.Value, blocks3[1].Type);
    }

    [Fact]
    public void ItParsesMultiNamedArgFunctionCalls()
    {
        // Arrange
        var template1 = "x.y first=$foo second='bar'";
        var parameters = new ContextVariables();
        parameters.Set("foo", "fooValue");

        // Act
        var blocks1 = this._target.Tokenize(template1);

        // Assert
        Assert.Equal(3, blocks1.Count);

        var firstBlock = blocks1[0];
        var secondBlock = blocks1[1] as NamedArgBlock;
        var thirdBlock = blocks1[2] as NamedArgBlock;

        Assert.Equal("x.y", firstBlock.Content);
        Assert.Equal(BlockTypes.FunctionId, firstBlock.Type);

        Assert.Equal("first=$foo", secondBlock?.Content);
        Assert.Equal(BlockTypes.NamedArg, secondBlock?.Type);
        Assert.Equal("first", secondBlock?.Name);
        Assert.Equal("fooValue", secondBlock?.GetValue(parameters));

        Assert.Equal("second='bar'", thirdBlock?.Content);
        Assert.Equal(BlockTypes.NamedArg, thirdBlock?.Type);
        Assert.Equal("second", thirdBlock?.Name);
        Assert.Equal("bar", thirdBlock?.GetValue(parameters));
    }

    [Fact]
    public void ItSupportsEscaping()
    {
        // Arrange
        var template = "func 'f\\'oo'";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(2, blocks.Count);
        Assert.Equal("func", blocks[0].Content);
        Assert.Equal("'f\'oo'", blocks[1].Content);
    }

    [Fact]
    public void ItSupportsEscapingNamedArgs()
    {
        // Arrange
        var template = "func name='f\\'oo'";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(2, blocks.Count);
        Assert.Equal("func", blocks[0].Content);
        Assert.Equal("name='f\'oo'", blocks[1].Content);
        var namedArg = blocks[1] as NamedArgBlock;
        Assert.NotNull(namedArg);
        Assert.Equal("f'oo", namedArg.GetValue(null));
    }

    [Fact]
    public void ItSupportsSpacesInNamedArguments()
    {
        // Arrange
        var template = "func name = 'foo'";

        // Act
        var blocks = this._target.Tokenize(template);

        // Assert
        Assert.Equal(2, blocks.Count);
        Assert.Equal("func", blocks[0].Content);
        Assert.Equal("name='foo'", blocks[1].Content);
        var namedArg = blocks[1] as NamedArgBlock;
        Assert.NotNull(namedArg);
        Assert.Equal("foo", namedArg.GetValue(null));
        Assert.Equal("name", namedArg.Name);
    }

    [Theory]
    [InlineData(@"call 'f\\'xy'")]
    [InlineData(@"call 'f\\'x")]
    [InlineData("f name")]
    public void ItThrowsWhenSeparatorsAreMissing(string template)
    {
        // Act & Assert
        Assert.Throws<SKException>(() => this._target.Tokenize(template));
    }

    [Theory]
    [InlineData("f a =", "A function named argument must contain a quoted value or variable after the '=' character.")]
    [InlineData("f a='b' arg2", "A function named argument must contain a name and value separated by a '=' character.")]
    public void ItThrowsWhenArgValueIsMissing(string template, string expectedErrorMessage)
    {
        // Act & Assert
        var exception = Assert.Throws<SKException>(() => this._target.Tokenize(template));
        Assert.Equal(expectedErrorMessage, exception.Message);
    }
}
