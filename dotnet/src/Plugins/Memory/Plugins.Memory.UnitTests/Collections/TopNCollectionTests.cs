// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.Memory.Collections;
using Xunit;

namespace SemanticKernel.Plugins.Memory.UnitTests.Collections;

/// <summary>
/// Contains tests for the <see cref="TopNCollection{T}"/> class.
/// </summary>
public class TopNCollectionTests
{
    private const int MaxItemsCount = 5;

    [Fact]
    public void ItResetsCollectionCorrectly()
    {
        // Arrange
        const int ExpectedItemsCount = 0;

        var topNCollection = this.GetTestCollection(MaxItemsCount);

        // Act
        topNCollection.Reset();

        // Assert
        Assert.Equal(ExpectedItemsCount, topNCollection.Count);
    }

    [Fact]
    public void ItKeepsMaxItemsCountWhenMoreItemsWereAdded()
    {
        // Arrange
        const int ExpectedCollectionCount = 5;

        // Act
        var topNCollection = this.GetTestCollection(ExpectedCollectionCount);

        // Assert
        Assert.Equal(ExpectedCollectionCount, topNCollection.Count);
    }

    [Fact]
    public void ItSortsCollectionByScoreInDescendingOrder()
    {
        // Arrange
        var topNCollection = this.GetTestCollection(MaxItemsCount);

        // Act
        topNCollection.SortByScore();

        // Assert
        for (var i = 0; i < topNCollection.Count - 1; i++)
        {
            Assert.True(topNCollection[i].Score > topNCollection[i + 1].Score);
        }
    }

    private TopNCollection<int> GetTestCollection(int maxItemsCount)
    {
        return new TopNCollection<int>(maxItemsCount)
        {
            new ScoredValue<int>(1, 0.5),
            new ScoredValue<int>(2, 0.6),
            new ScoredValue<int>(3, 0.4),
            new ScoredValue<int>(4, 0.2),
            new ScoredValue<int>(5, 0.9),
            new ScoredValue<int>(6, 0.1),
        };
    }
}
