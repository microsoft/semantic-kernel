// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;
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
        const int invalidCapacity = -1;

        var action = () =>
        {
            var minHeap = new MinHeap<int>(MinValue, invalidCapacity);
        };

        // Act
        var exception = Assert.Throws<ValidationException>(() => action());

        // Assert
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, exception.ErrorCode);
        Assert.Equal("OutOfRange: MinHeap capacity must be greater than 0.", exception.Message);
    }

    [Fact]
    public void ItAddsItemsInCorrectOrder()
    {
        // Arrange
        const int expectedTopItem = 1;
        const int expectedCount = 3;

        // Act
        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Assert
        Assert.Equal(expectedTopItem, minHeap.Top);
        Assert.Equal(expectedCount, minHeap.Count);
    }

    [Fact]
    public void ItErasesItemsCorrectly()
    {
        // Arrange
        const int expectedCount = 0;
        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        minHeap.Erase();

        // Assert
        Assert.Equal(expectedCount, minHeap.Count);
    }

    [Fact]
    public void ItReturnsItemsOnBufferDetaching()
    {
        // Arrange
        const int expectedHeapCount = 0;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        var items = minHeap.DetachBuffer();

        // Assert
        Assert.True(items.Length > 0);
        Assert.Equal(expectedHeapCount, minHeap.Count);
    }

    [Fact]
    public void ItThrowsExceptionOnAddingItemsAtInvalidIndex()
    {
        // Arrange
        const int startIndex = 4;

        var items = new List<int> { 3, 1, 2 };
        var minHeap = new MinHeap<int>(MinValue);

        var action = () => { minHeap.Add(items, startIndex); };

        // Act
        var exception = Assert.Throws<ValidationException>(() => action());

        // Assert
        Assert.Equal(ValidationException.ErrorCodes.OutOfRange, exception.ErrorCode);
        Assert.Equal("OutOfRange: startAt value must be less than items count.", exception.Message);
    }

    [Fact]
    public void ItRemovesTopItemCorrectly()
    {
        // Arrange
        const int expectedTopItem = 2;
        const int expectedHeapCount = 2;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        minHeap.RemoveTop();

        // Assert
        Assert.Equal(expectedTopItem, minHeap.Top);
        Assert.Equal(expectedHeapCount, minHeap.Count);
    }

    [Fact]
    public void ItRemovesAllItemsCorrectly()
    {
        // Arrange
        const int expectedHeapCount = 0;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        var items = minHeap.RemoveAll().ToList();

        // Assert
        Assert.Equal(1, items[0]);
        Assert.Equal(2, items[1]);
        Assert.Equal(3, items[2]);

        Assert.Equal(expectedHeapCount, minHeap.Count);
    }

    [Fact]
    public void ItEnsuresCapacityToExpectedValue()
    {
        // Arrange
        const int expectedCapacity = 16;

        var minHeap = new MinHeap<int>(MinValue);

        // Act
        minHeap.EnsureCapacity(expectedCapacity);

        // Assert
        Assert.Equal(expectedCapacity, minHeap.Capacity);
    }
}
