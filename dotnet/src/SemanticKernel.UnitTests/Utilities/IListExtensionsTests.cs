// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

public class IListExtensionsTests
{
    [Fact]
    public void ItShouldAddRangeOfElementsToTargetList()
    {
        // Arrange
        IList<int> target = [];
        int[] source = [1, 2, 3];

        // Act
        target.AddRange(source);

        // Assert
        Assert.Equal(3, target.Count);
        Assert.Equal(1, target[0]);
        Assert.Equal(2, target[1]);
        Assert.Equal(3, target[2]);
    }
}
