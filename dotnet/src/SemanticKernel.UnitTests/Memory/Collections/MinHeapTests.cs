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
        const int InvalidCapacity = -1;

        void Action()
        {
            var minHeap = new MinHeap<int>(MinValue, InvalidCapacity);
        }

        // Act
        var exception = Assert.Throws<ArgumentOutOfRangeException>("capacity", Action);

        // Assert
        Assert.Equal(-1, exception.ActualValue);
    }

    [Fact]
    public void ItAddsItemsInCorrectOrder()
    {
        // Arrange
        const int ExpectedTopItem = 1;
        const int ExpectedCount = 3;

        // Act
        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Assert
        Assert.Equal(ExpectedTopItem, minHeap.Top);
        Assert.Equal(ExpectedCount, minHeap.Count);
    }

    [Fact]
    public void ItErasesItemsCorrectly()
    {
        // Arrange
        const int ExpectedCount = 0;
        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        minHeap.Erase();

        // Assert
        Assert.Equal(ExpectedCount, minHeap.Count);
    }

    [Fact]
    public void ItReturnsItemsOnBufferDetaching()
    {
        // Arrange
        const int ExpectedHeapCount = 0;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        var items = minHeap.DetachBuffer();

        // Assert
        Assert.True(items.Length > 0);
        Assert.Equal(ExpectedHeapCount, minHeap.Count);
    }

    [Fact]
    public void ItThrowsExceptionOnAddingItemsAtInvalidIndex()
    {
        // Arrange
        const int StartIndex = 4;

        var items = new List<int> { 3, 1, 2 };
        var minHeap = new MinHeap<int>(MinValue);

        void action() { minHeap.Add(items, StartIndex); }

        // Act
        var exception = Assert.Throws<ArgumentOutOfRangeException>("startAt", () => action());

        // Assert
        Assert.Equal(StartIndex, exception.ActualValue);
    }

    [Fact]
    public void ItRemovesTopItemCorrectly()
    {
        // Arrange
        const int ExpectedTopItem = 2;
        const int ExpectedHeapCount = 2;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        minHeap.RemoveTop();

        // Assert
        Assert.Equal(ExpectedTopItem, minHeap.Top);
        Assert.Equal(ExpectedHeapCount, minHeap.Count);
    }

    [Fact]
    public void ItRemovesAllItemsCorrectly()
    {
        // Arrange
        const int ExpectedHeapCount = 0;

        var minHeap = new MinHeap<int>(MinValue) { 3, 1, 2 };

        // Act
        var items = minHeap.RemoveAll().ToList();

        // Assert
        Assert.Equal(1, items[0]);
        Assert.Equal(2, items[1]);
        Assert.Equal(3, items[2]);

        Assert.Equal(ExpectedHeapCount, minHeap.Count);
    }

    [Fact]
    public void ItEnsuresCapacityToExpectedValue()
    {
        // Arrange
        const int ExpectedCapacity = 16;

        var minHeap = new MinHeap<int>(MinValue);

        // Act
        minHeap.EnsureCapacity(ExpectedCapacity);

        // Assert
        Assert.Equal(ExpectedCapacity, minHeap.Capacity);
    }
}
