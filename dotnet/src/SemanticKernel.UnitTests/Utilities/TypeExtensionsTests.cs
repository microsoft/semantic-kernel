// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Xunit;
using TypeExtensions = System.TypeExtensions;

namespace SemanticKernel.UnitTests.Utilities;

/// <summary>
/// Unit tests for <see cref="TypeExtensions"/> class.
/// </summary>
public sealed class TypeExtensionsTests
{
    [Theory]
    [InlineData(null, typeof(object), false)]
    [InlineData(typeof(TestType), typeof(object), false)]
    [InlineData(typeof(Task<TestType>), typeof(TestType), true)]
    [InlineData(typeof(TestType?), typeof(TestType), true)]
    [InlineData(typeof(ValueTask<TestType>), typeof(TestType), true)]
    [InlineData(typeof(IEnumerable<TestType>), typeof(List<TestType>), true)]
    [InlineData(typeof(IList<TestType>), typeof(List<TestType>), true)]
    [InlineData(typeof(ICollection<TestType>), typeof(List<TestType>), true)]
    [InlineData(typeof(IDictionary<string, TestType>), typeof(Dictionary<string, TestType>), true)]
    public void TryGetGenericResultTypeWorksCorrectly(Type? type, Type expectedType, bool expectedResult)
    {
        // Arrange & Act
        var result = type.TryGetGenericResultType(out var resultType);

        // Assert
        Assert.Equal(expectedResult, result);
        Assert.Equal(expectedType, resultType);
    }

    private struct TestType { }
}
