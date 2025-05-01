// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

public class VectorStoreRecordMappingTests
{
    [Theory]
    [InlineData(typeof(List<string>))]
    [InlineData(typeof(ICollection<string>))]
    [InlineData(typeof(IEnumerable<string>))]
    [InlineData(typeof(IList<string>))]
    [InlineData(typeof(IReadOnlyCollection<string>))]
    [InlineData(typeof(IReadOnlyList<string>))]
    [InlineData(typeof(string[]))]
    [InlineData(typeof(IEnumerable))]
    [InlineData(typeof(ArrayList))]
    public void CreateEnumerableCanCreateEnumerablesOfAllRequiredTypes(Type expectedType)
    {
        // Arrange.
        IEnumerable<string> input = new List<string> { "one", "two", "three", "four" };

        // Act.
        var actual = VectorStoreRecordMapping.CreateEnumerable(input, expectedType);

        // Assert.
        Assert.True(expectedType.IsAssignableFrom(actual!.GetType()));
    }

    [Theory]
    [InlineData(typeof(List<string>))]
    [InlineData(typeof(ICollection<string>))]
    [InlineData(typeof(IEnumerable<string>))]
    [InlineData(typeof(IList<string>))]
    [InlineData(typeof(IReadOnlyCollection<string>))]
    [InlineData(typeof(IReadOnlyList<string>))]
    [InlineData(typeof(string[]))]
    [InlineData(typeof(IEnumerable))]
    [InlineData(typeof(ArrayList))]
    public void CreateEnumerableCanCreateEnumerablesOfAllRequiredTypesUsingObjectEnumerable(Type expectedType)
    {
        // Arrange.
        IEnumerable<object> input = new List<object> { "one", "two", "three", "four" };

        // Act.
        var actual = VectorStoreRecordMapping.CreateEnumerable(input, expectedType);

        // Assert.
        Assert.True(expectedType.IsAssignableFrom(actual!.GetType()));
    }

    [Theory]
    [InlineData(typeof(string))]
    [InlineData(typeof(HashSet<string>))]
    [InlineData(typeof(ISet<string>))]
    [InlineData(typeof(Dictionary<string, string>))]
    [InlineData(typeof(Stack<string>))]
    [InlineData(typeof(Queue<string>))]
    public void CreateEnumerableThrowsForUnsupportedType(Type expectedType)
    {
        // Arrange.
        IEnumerable<string> input = new List<string> { "one", "two", "three", "four" };

        // Act & Assert.
        Assert.Throws<NotSupportedException>(() => VectorStoreRecordMapping.CreateEnumerable(input, expectedType));
    }
}
