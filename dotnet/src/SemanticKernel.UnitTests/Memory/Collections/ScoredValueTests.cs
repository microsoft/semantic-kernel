// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory.Collections;
using Xunit;

namespace SemanticKernel.UnitTests.Memory.Collections;

/// <summary>
/// Contains tests for the <see cref="ScoredValue{T}"/> struct.
/// </summary>
public class ScoredValueTests
{
    [Fact]
    public void InEqualScenarioComparisonOperatorsWorkCorrectly()
    {
        // Arrange
        var first = new ScoredValue<int>(1, 1);
        var second = new ScoredValue<int>(1, 1);

        // Act & Assert
        Assert.False(first < second);
        Assert.False(first > second);

        Assert.True(first <= second);
        Assert.True(first >= second);

        Assert.False(first != second);
        Assert.True(first == second);
    }

    [Theory]
    [InlineData(1, 1, 1, 2)]
    [InlineData(1, 1, 2, 1)]
    public void InNotEqualScenarioComparisonOperatorsWorkCorrectly(int firstValue, double firstScore, int secondValue, double secondScore)
    {
        // Arrange
        var first = new ScoredValue<int>(firstValue, firstScore);
        var second = new ScoredValue<int>(secondValue, secondScore);

        // Act & Assert
        Assert.True(first < second);
        Assert.False(first > second);

        Assert.True(first <= second);
        Assert.False(first >= second);

        Assert.True(first != second);
        Assert.False(first == second);
    }
}
