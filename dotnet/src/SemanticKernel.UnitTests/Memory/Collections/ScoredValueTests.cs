// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory.Collections;
using Xunit;

namespace SemanticKernel.UnitTests.Memory.Collections;

/// <summary>
/// Contains tests for the <see cref="ScoredValue{T}"/> struct.
/// </summary>
public class ScoredValueTests
{
    [Theory]
    [InlineData(1, 1.1, 1, 1.1, true)]
    [InlineData(1, 2.2, 1, 2.2, true)]
    [InlineData(2, 1.1, 1, 1.1, false)]
    [InlineData(1, 2.2, 1, 1.1, false)]
    public void EqualOperatorWorksCorrectly(int firstValue, double firstScore, int secondValue, double secondScore, bool expectedResult)
    {
        // Arrange
        var first = new ScoredValue<int>(firstValue, firstScore);
        var second = new ScoredValue<int>(secondValue, secondScore);

        // Act
        var actualResult = first == second;

        // Assert
        Assert.Equal(expectedResult, actualResult);
    }

    [Theory]
    [InlineData(1, 1.1, 1, 1.1, false)]
    [InlineData(1, 2.2, 1, 2.2, false)]
    [InlineData(2, 1.1, 1, 1.1, true)]
    [InlineData(1, 2.2, 1, 1.1, true)]
    public void NotEqualOperatorWorksCorrectly(int firstValue, double firstScore, int secondValue, double secondScore, bool expectedResult)
    {
        // Arrange
        var first = new ScoredValue<int>(firstValue, firstScore);
        var second = new ScoredValue<int>(secondValue, secondScore);

        // Act
        var actualResult = first != second;

        // Assert
        Assert.Equal(expectedResult, actualResult);
    }

    [Theory]
    [InlineData(1, 1.0, 1, 1.1, true)]
    [InlineData(1, 1.1, 1, 1.1, true)]
    public void LessThanOperatorWorksCorrectly(int firstValue, double firstScore, int secondValue, double secondScore, bool expectedResult)
    {
        // Arrange
        var first = new ScoredValue<int>(firstValue, firstScore);
        var second = new ScoredValue<int>(secondValue, secondScore);

        // Act
        var actualResult = first < second;

        // Assert
        Assert.Equal(expectedResult, actualResult);
    }
}
