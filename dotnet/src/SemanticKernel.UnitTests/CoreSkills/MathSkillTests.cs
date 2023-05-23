// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.CoreSkills;

public class MathSkillTests
{
    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var _ = new MathSkill();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportSkill(new MathSkill(), "math");
    }

    [Theory]
    [InlineData("10", "10", "20")]
    [InlineData("0", "10", "10")]
    [InlineData("0", "-10", "-10")]
    [InlineData("10", "0", "10")]
    [InlineData("-1", "10", "9")]
    [InlineData("-10", "10", "0")]
    [InlineData("-192", "13", "-179")]
    [InlineData("-192", "-13", "-205")]
    public async Task AddAsyncWhenValidParametersShouldSucceedAsync(string initialValue, string amount, string expectedResult)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["Amount"] = amount
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new MathSkill();

        // Act
        string result = await target.AddAsync(initialValue, context);

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Theory]
    [InlineData("10", "10", "0")]
    [InlineData("0", "10", "-10")]
    [InlineData("10", "0", "10")]
    [InlineData("100", "-10", "110")]
    [InlineData("100", "102", "-2")]
    [InlineData("-1", "10", "-11")]
    [InlineData("-10", "10", "-20")]
    [InlineData("-192", "13", "-205")]
    public async Task SubtractAsyncWhenValidParametersShouldSucceedAsync(string initialValue, string amount, string expectedResult)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["Amount"] = amount
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new MathSkill();

        // Act
        string result = await target.SubtractAsync(initialValue, context);

        // Assert
        Assert.Equal(expectedResult, result);
    }

    [Theory]
    [InlineData("$0")]
    [InlineData("one hundred")]
    [InlineData("20..,,2,1")]
    [InlineData(".2,2.1")]
    [InlineData("0.1.0")]
    [InlineData("00-099")]
    [InlineData("¹²¹")]
    [InlineData("2²")]
    [InlineData("zero")]
    [InlineData("-100 units")]
    [InlineData("1 banana")]
    public async Task AddAsyncWhenInvalidInitialValueShouldThrowAsync(string initialValue)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["Amount"] = "1"
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new MathSkill();

        // Act
        var exception = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () =>
        {
            await target.AddAsync(initialValue, context);
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(initialValue, exception.ActualValue);
        Assert.Equal("initialValueText", exception.ParamName);
    }

    [Theory]
    [InlineData("$0")]
    [InlineData("one hundred")]
    [InlineData("20..,,2,1")]
    [InlineData(".2,2.1")]
    [InlineData("0.1.0")]
    [InlineData("00-099")]
    [InlineData("¹²¹")]
    [InlineData("2²")]
    [InlineData("zero")]
    [InlineData("-100 units")]
    [InlineData("1 banana")]
    public async Task AddAsyncWhenInvalidAmountShouldThrowAsync(string amount)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["Amount"] = amount
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new MathSkill();

        // Act
        var exception = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () =>
        {
            await target.AddAsync("1", context);
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(amount, exception.ActualValue);
        Assert.Equal("context", exception.ParamName);
    }

    [Theory]
    [InlineData("$0")]
    [InlineData("one hundred")]
    [InlineData("20..,,2,1")]
    [InlineData(".2,2.1")]
    [InlineData("0.1.0")]
    [InlineData("00-099")]
    [InlineData("¹²¹")]
    [InlineData("2²")]
    [InlineData("zero")]
    [InlineData("-100 units")]
    [InlineData("1 banana")]
    public async Task SubtractAsyncWhenInvalidInitialValueShouldThrowAsync(string initialValue)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["Amount"] = "1"
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new MathSkill();

        // Act
        var exception = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () =>
        {
            await target.SubtractAsync(initialValue, context);
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(initialValue, exception.ActualValue);
        Assert.Equal("initialValueText", exception.ParamName);
    }

    [Theory]
    [InlineData("$0")]
    [InlineData("one hundred")]
    [InlineData("20..,,2,1")]
    [InlineData(".2,2.1")]
    [InlineData("0.1.0")]
    [InlineData("00-099")]
    [InlineData("¹²¹")]
    [InlineData("2²")]
    [InlineData("zero")]
    [InlineData("-100 units")]
    [InlineData("1 banana")]
    public async Task SubtractAsyncWhenInvalidAmountShouldThrowAsync(string amount)
    {
        // Arrange
        var variables = new ContextVariables
        {
            ["Amount"] = amount
        };

        var context = new SKContext(variables, new Mock<ISemanticTextMemory>().Object, new Mock<IReadOnlySkillCollection>().Object, new Mock<ILogger>().Object);
        var target = new MathSkill();

        // Act
        var exception = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(async () =>
        {
            await target.SubtractAsync("1", context);
        });

        // Assert
        Assert.NotNull(exception);
        Assert.Equal(amount, exception.ActualValue);
        Assert.Equal("context", exception.ParamName);
    }
}
