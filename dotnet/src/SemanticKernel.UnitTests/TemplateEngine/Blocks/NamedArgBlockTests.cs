// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class NamedArgBlockTests
{
    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new NamedArgBlock("a=$b", NullLoggerFactory.Instance);

        // Assert
        Assert.Equal(BlockTypes.NamedArg, target.Type);
    }

    [Fact]
    public void ItTrimsSpaces()
    {
        // Act + Assert
        Assert.Equal("a=$b", new NamedArgBlock("  a=$b  ", NullLoggerFactory.Instance).Content);
    }

    [Theory]
    [InlineData("0='val'", true)]
    [InlineData("1='val'", true)]
    [InlineData("a='val'", true)]
    [InlineData("_='val'", true)]
    [InlineData("01='val'", true)]
    [InlineData("01a='val'", true)]
    [InlineData("a01='val'", true)]
    [InlineData("_0='val'", true)]
    [InlineData("a01_='val'", true)]
    [InlineData("_a01='val'", true)]
    [InlineData(".='val'", false)]
    [InlineData("-='val'", false)]
    [InlineData("a b='val'", false)]
    [InlineData("a\nb='val'", false)]
    [InlineData("a\tb='val'", false)]
    [InlineData("a\rb='val'", false)]
    [InlineData("a.b='val'", false)]
    [InlineData("a,b='val'", false)]
    [InlineData("a-b='val'", false)]
    [InlineData("a+b='val'", false)]
    [InlineData("a~b='val'", false)]
    [InlineData("a`b='val'", false)]
    [InlineData("a!b='val'", false)]
    [InlineData("a@b='val'", false)]
    [InlineData("a#b='val'", false)]
    [InlineData("a$b='val'", false)]
    [InlineData("a%b='val'", false)]
    [InlineData("a^b='val'", false)]
    [InlineData("a*b='val'", false)]
    [InlineData("a(b='val'", false)]
    [InlineData("a)b='val'", false)]
    [InlineData("a|b='val'", false)]
    [InlineData("a{b='val'", false)]
    [InlineData("a}b='val'", false)]
    [InlineData("a[b='val'", false)]
    [InlineData("a]b='val'", false)]
    [InlineData("a:b='val'", false)]
    [InlineData("a;b='val'", false)]
    [InlineData("a'b='val'", false)]
    [InlineData("a\"b='val'", false)]
    [InlineData("a<b='val'", false)]
    [InlineData("a>b='val'", false)]
    [InlineData("a/b='val'", false)]
    [InlineData("a\\b='val'", false)]
    public void ArgNameAllowsUnderscoreLettersAndDigits(string name, bool isValid)
    {
        // Arrange
        var target = new NamedArgBlock($" {name} ");

        // Act + Assert
        Assert.Equal(isValid, target.IsValid(out _));
    }

    [Fact]
    public void ArgValueNeedsQuoteOrDollarSignPrefix()
    {
        // Arrange
        var target = new NamedArgBlock("a=b");

        // Act + Assert
        Assert.False(target.IsValid(out _));
    }

    [Theory]
    [InlineData("0='val'", true)]
    [InlineData("0=\"val\"", true)]
    [InlineData("0='val\"", false)]
    [InlineData("0=\"val'", false)]
    public void ArgValueAllowsConsistentlyQuotedValues(string name, bool isValid)
    {
        // Arrange
        var target = new NamedArgBlock($" {name} ");

        // Act + Assert
        Assert.Equal(isValid, target.IsValid(out _));
    }

    [Theory]
    [InlineData("0", true)]
    [InlineData("1", true)]
    [InlineData("a", true)]
    [InlineData("_", true)]
    [InlineData("01", true)]
    [InlineData("01a", true)]
    [InlineData("a01", true)]
    [InlineData("_0", true)]
    [InlineData("a01_", true)]
    [InlineData("_a01", true)]
    [InlineData(".", false)]
    [InlineData("-", false)]
    [InlineData("a b", false)]
    [InlineData("a\nb", false)]
    [InlineData("a\tb", false)]
    [InlineData("a\rb", false)]
    [InlineData("a.b", false)]
    [InlineData("a,b", false)]
    [InlineData("a-b", false)]
    [InlineData("a+b", false)]
    [InlineData("a~b", false)]
    [InlineData("a`b", false)]
    [InlineData("a!b", false)]
    [InlineData("a@b", false)]
    [InlineData("a#b", false)]
    [InlineData("a$b", false)]
    [InlineData("a%b", false)]
    [InlineData("a^b", false)]
    [InlineData("a*b", false)]
    [InlineData("a(b", false)]
    [InlineData("a)b", false)]
    [InlineData("a|b", false)]
    [InlineData("a{b", false)]
    [InlineData("a}b", false)]
    [InlineData("a[b", false)]
    [InlineData("a]b", false)]
    [InlineData("a:b", false)]
    [InlineData("a;b", false)]
    [InlineData("a'b", false)]
    [InlineData("a\"b", false)]
    [InlineData("a<b", false)]
    [InlineData("a>b", false)]
    [InlineData("a/b", false)]
    [InlineData("a\\b", false)]
    public void ArgValueAllowsVariablesWithUnderscoreLettersAndDigits(string name, bool isValid)
    {
        // Arrange
        var target = new NamedArgBlock($"a=${name}");
        var variables = new ContextVariables { [name] = "value" };

        // Act + Assert
        Assert.Equal(isValid, target.IsValid(out _));
    }

    [Fact]
    public void ItRequiresOneEquals()
    {
        // Arrange
        var target1 = new NamedArgBlock("a='b'");
        var target2 = new NamedArgBlock("a=$b");
        var target3 = new NamedArgBlock("a=\"b\"");
        Assert.Throws<SKException>(() => new NamedArgBlock("foo"));
        Assert.Throws<SKException>(() => new NamedArgBlock("foo=$bar=$baz"));

        // Act + Assert
        Assert.True(target1.IsValid(out _));
        Assert.True(target2.IsValid(out _));
        Assert.True(target3.IsValid(out _));
    }
}
