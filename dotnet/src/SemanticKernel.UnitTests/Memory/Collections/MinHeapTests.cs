// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Memory.Collections;
using Xunit;

namespace SemanticKernel.UnitTests.Memory.Collections;

/// <summary>
/// Contains tests for the <see cref="MinHeap{T}"/> class.
/// </summary>
public class MinHeapTests
{
    private const int MinValue = 1;

    [Fact]
    public void ItThrowsExceptionWhenCapacityIsInvalid()
    {
        // Arrange
        const int INVALID_CAPACITY = -1;

        var action = () =>
        {
            var minHeap = new MinHeap<int>(MinValue, INVALID_CAPACITY);
        };

        // Act
        var exception = Assert.Throws<ArgumentOutOfRangeException>("capacity", () => action());

        // Assert
        Assert.Equal(-1, exception.ActualValue);
    }

    [Fact]
    public void ItAddsItemsInCorrectOrder()
    {
        // Arrange
        const int EXPECTED_TOP_ITEM = 1;
        const int EXPECTED_COUNT = 3;

        // Act
        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Assert
        Assert.Equal(EXPECTED_TOP_ITEM, minHeap.Top);
        Assert.Equal(EXPECTED_COUNT, minHeap.Count);
    }

    [Fact]
    public void ItErasesItemsCorrectly()
    {
        // Arrange
        const int EXPECTED_COUNT = 0;
        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        minHeap.Erase();

        // Assert
        Assert.Equal(EXPECTED_COUNT, minHeap.Count);
    }

    [Fact]
    public void ItReturnsItemsOnBufferDetaching()
    {
        // Arrange
        const int EXPECTED_HEAP_COUNT = 0;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        var items = minHeap.DetachBuffer();

        // Assert
        Assert.True(items.Length > 0);
        Assert.Equal(EXPECTED_HEAP_COUNT, minHeap.Count);
    }

    [Fact]
    public void ItThrowsExceptionOnAddingItemsAtInvalidIndex()
    {
        // Arrange
        const int START_INDEX = 4;

        var items = new List<int> { 3, 1, 2 };
        var minHeap = new MinHeap<int>(MinValue);

        var action = () => { minHeap.Add(items, START_INDEX); };

        // Act
        var exception = Assert.Throws<ArgumentOutOfRangeException>("startAt", () => action());

        // Assert
        Assert.Equal(START_INDEX, exception.ActualValue);
    }

    [Fact]
    public void ItRemovesTopItemCorrectly()
    {
        // Arrange
        const int EXPECTED_TOP_ITEM = 2;
        const int EXPECTED_HEAP_COUNT = 2;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        minHeap.RemoveTop();

        // Assert
        Assert.Equal(EXPECTED_TOP_ITEM, minHeap.Top);
        Assert.Equal(EXPECTED_HEAP_COUNT, minHeap.Count);
    }

    [Fact]
    public void ItRemovesAllItemsCorrectly()
    {
        // Arrange
        const int EXPECTED_HEAP_COUNT = 0;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        var items = minHeap.RemoveAll().ToList();

        // Assert
        Assert.Equal(1, items[0]);
        Assert.Equal(2, items[1]);
        Assert.Equal(3, items[2]);

        Assert.Equal(EXPECTED_HEAP_COUNT, minHeap.Count);
    }

    [Fact]
    public void ItEnsuresCapacityToExpectedValue()
    {
        // Arrange
        const int EXPECTED_CAPACITY = 16;

        var minHeap = new MinHeap<int>(MinValue);

        // Act
        minHeap.EnsureCapacity(EXPECTED_CAPACITY);

        // Assert
        Assert.Equal(EXPECTED_CAPACITY, minHeap.Capacity);
    }
}
