// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
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
        var kernel = KernelBuilder.Create();

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
}
