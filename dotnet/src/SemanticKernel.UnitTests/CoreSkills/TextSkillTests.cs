// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.CoreSkills;

public class TextSkillTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new TextSkill();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportSkill(new TextSkill(), "text");
    }

    [Fact]
    public void ItCanTrim()
    {
        // Arrange
        var skill = new TextSkill();

        // Act
        var result = skill.Trim("  hello world  ");

        // Assert
        Assert.Equal("hello world", result);
    }

    [Fact]
    public void ItCanTrimStart()
    {
        // Arrange
        var skill = new TextSkill();

        // Act
        var result = skill.TrimStart("  hello world  ");

        // Assert
        Assert.Equal("hello world  ", result);
    }

    [Fact]
    public void ItCanTrimEnd()
    {
        // Arrange
        var skill = new TextSkill();

        // Act
        var result = skill.TrimEnd("  hello world  ");

        // Assert
        Assert.Equal("  hello world", result);
    }

    [Fact]
    public void ItCanUppercase()
    {
        // Arrange
        var skill = new TextSkill();

        // Act
        var result = skill.Uppercase("hello world");

        // Assert
        Assert.Equal("HELLO WORLD", result);
    }

    [Fact]
    public void ItCanLowercase()
    {
        // Arrange
        var skill = new TextSkill();

        // Act
        var result = skill.Lowercase("HELLO WORLD");

        // Assert
        Assert.Equal("hello world", result);
    }

    [Theory]
    [InlineData("hello world ", 12)]
    [InlineData("hello World", 11)]
    [InlineData("HELLO", 5)]
    [InlineData("World", 5)]
    [InlineData("", 0)]
    [InlineData(" ", 1)]
    [InlineData(null, 0)]
    public void ItCanLength(string textToLength, int expectedLength)
    {
        // Arrange
        var target = new TextSkill();

        // Act
        var result = target.Length(textToLength);

        // Assert
        Assert.Equal(expectedLength.ToString(System.Globalization.CultureInfo.InvariantCulture), result);
    }

    [Theory]
    [InlineData("hello world", "hello world")]
    [InlineData("hello World", "hello World")]
    [InlineData("HELLO", "HELLO")]
    [InlineData("World", "World")]
    [InlineData("", "")]
    [InlineData(" ", " ")]
    [InlineData(null, "")]
    public void ItCanConcat(string textToConcat, string text2ToConcat)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["input2"] = text2ToConcat
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new TextSkill();
        var expected = string.Concat(textToConcat, text2ToConcat);

        // Act
        string result = target.Concat(textToConcat, context);

        // Assert
        Assert.Equal(expected, result);
    }
}
