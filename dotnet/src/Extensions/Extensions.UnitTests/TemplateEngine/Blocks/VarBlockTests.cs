// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class VarBlockTests
{
    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new VarBlock("");

        // Assert
        Assert.Equal(BlockTypes.Variable, target.Type);
    }

    [Fact]
    public void ItTrimsSpaces()
    {
        // Act + Assert
        Assert.Equal("$", new VarBlock("  $  ").Content);
    }

    [Fact]
    public void ItIgnoresSpacesAround()
    {
        // Act
        var target = new VarBlock("  $var \n ");

        // Assert
        Assert.Equal("$var", target.Content);
    }

    [Fact]
    public void ItRendersToEmptyStringWithoutVariables()
    {
        // Arrange
        var target = new VarBlock("  $var \n ");

        // Act
        var result = target.Render(null);

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void ItRendersToEmptyStringIfVariableIsMissing()
    {
        // Arrange
        var target = new VarBlock("  $var \n ");
        var variables = new ContextVariables
        {
            ["foo"] = "bar"
        };

        // Act
        var result = target.Render(variables);

        // Assert
        Assert.Equal(string.Empty, result);
    }

    [Fact]
    public void ItRendersToVariableValueWhenAvailable()
    {
        // Arrange
        var target = new VarBlock("  $var \n ");
        var variables = new ContextVariables
        {
            ["foo"] = "bar",
            ["var"] = "able",
        };

        // Act
        var result = target.Render(variables);

        // Assert
        Assert.Equal("able", result);
    }

    [Fact]
    public void ItThrowsIfTheVarNameIsEmpty()
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["foo"] = "bar",
            ["var"] = "able",
        };
        var target = new VarBlock(" $ ");

        // Act + Assert
        Assert.Throws<SKException>(() => target.Render(variables));
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
    public void ItAllowsUnderscoreLettersAndDigits(string name, bool isValid)
    {
        // Arrange
        var target = new VarBlock($" ${name} ");
        var variables = new ContextVariables { [name] = "value" };

        // Act
        var result = target.Render(variables);

        // Assert
        Assert.Equal(isValid, target.IsValid(out _));
        if (isValid) { Assert.Equal("value", result); }
    }
}
