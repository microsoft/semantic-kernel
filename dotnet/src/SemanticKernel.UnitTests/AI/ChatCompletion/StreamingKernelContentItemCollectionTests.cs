// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

public class StreamingKernelContentItemCollectionTests
{
    [Fact]
    public void ItShouldBeEmptyByDefault()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();

        // Assert
        Assert.Empty(collection);
    }

    [Fact]
    public void ItShouldBePossibleToAddItemToTheCollection()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item = new StreamingTextContent("fake-text");

        // Act
        collection.Add(item);

        // Assert
        Assert.Single(collection);
        Assert.Same(item, collection[0]);
    }

    [Fact]
    public void ItShouldBePossibleToAccessItemByIndex()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();

        var item1 = new StreamingTextContent("fake-text");
        collection.Add(item1);

        // Act
        var retrievedItem = collection[0];

        // Assert
        Assert.Same(item1, retrievedItem);
    }

    [Fact]
    public void ItShouldBeEmptyAfterClear()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection
        {
            new StreamingTextContent("fake-text")
        };

        // Act
        collection.Clear();

        // Assert
        Assert.Empty(collection);
    }

    [Fact]
    public void ItShouldContainItemAfterAdd()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item = new StreamingTextContent("fake-text");

        // Act
        collection.Add(item);

        // Assert
        Assert.Contains(item, collection);
    }

    [Fact]
    public void ItShouldCopyItemsToAnArray()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);
        collection.Add(item2);

        // Act
        var array = new StreamingKernelContent[2];
        collection.CopyTo(array, 0);

        // Assert
        Assert.Equal(new[] { item1, item2 }, array);
    }

    [Fact]
    public void ItShouldReturnIndexOfItem()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);
        collection.Add(item2);

        // Act
        var index = collection.IndexOf(item2);

        // Assert
        Assert.Equal(1, index);
    }

    [Fact]
    public void ItShouldInsertItemIntoCollection()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);

        // Act
        collection.Insert(0, item2);

        // Assert
        Assert.Equal(new[] { item2, item1 }, collection);
    }

    [Fact]
    public void ItShouldRemoveItemFromCollection()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);
        collection.Add(item2);

        // Act
        collection.Remove(item1);

        // Assert
        Assert.Equal(new[] { item2 }, collection);
    }

    [Fact]
    public void ItShouldRemoveItemAtSpecifiedIndex()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);
        collection.Add(item2);

        // Act
        collection.RemoveAt(0);

        // Assert
        Assert.Equal(new[] { item2 }, collection);
    }

    [Fact]
    public void ItIsNotReadOnly()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();

        // Assert
        Assert.False(((ICollection<StreamingKernelContent>)collection).IsReadOnly);
    }

    [Fact]
    public void ItShouldReturnEnumerator()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);
        collection.Add(item2);

        // Act
        var enumerator = ((IEnumerable)collection).GetEnumerator();

        // Assert
        Assert.True(enumerator.MoveNext());
        Assert.Same(item1, enumerator.Current);
        Assert.True(enumerator.MoveNext());
        Assert.Same(item2, enumerator.Current);
        Assert.False(enumerator.MoveNext());
    }

    [Fact]
    public void ItShouldReturnGenericEnumerator()
    {
        // Arrange
        var collection = new StreamingKernelContentItemCollection();
        var item1 = new StreamingTextContent("fake-text1");
        var item2 = new StreamingTextContent("fake-text2");
        collection.Add(item1);
        collection.Add(item2);

        // Act
        var enumerator = ((IEnumerable<StreamingKernelContent>)collection).GetEnumerator();

        // Assert
        Assert.True(enumerator.MoveNext());
        Assert.Same(item1, enumerator.Current);
        Assert.True(enumerator.MoveNext());
        Assert.Same(item2, enumerator.Current);
        Assert.False(enumerator.MoveNext());
    }
}
