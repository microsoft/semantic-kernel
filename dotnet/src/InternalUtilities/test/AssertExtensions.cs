// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace SemanticKernel.UnitTests;

internal static class AssertExtensions
{
    /// <summary>Asserts that an exception is an <see cref="ArgumentOutOfRangeException"/> with the specified values.</summary>
    public static void AssertIsArgumentOutOfRange(Exception? e, string expectedParamName, string expectedActualValue)
    {
        ArgumentOutOfRangeException aoore = Assert.IsType<ArgumentOutOfRangeException>(e);
        Assert.Equal(expectedActualValue, aoore.ActualValue);
        Assert.Equal(expectedParamName, aoore.ParamName);
    }
}
