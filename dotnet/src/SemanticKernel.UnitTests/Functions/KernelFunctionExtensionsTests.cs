// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionExtensionsTests
{
    [Theory]
    [ClassData(typeof(ComplexObjectTestData))]
    public async Task InvokeAsyncOfTShouldMatchFunctionResultValueAsync(object? expectedValue)
    {
        var testFunction = KernelFunctionFactory.CreateFromMethod(() => expectedValue, functionName: "Test");

        var kernel = new Kernel();
        var resultValueInvokeSignature2 = await testFunction.InvokeAsync<object>(kernel, new KernelArguments());

        Assert.Equal(expectedValue, resultValueInvokeSignature2);
    }

    public class ComplexObjectTestData : IEnumerable<object[]>
    {
        private readonly List<object?[]> _data = new()
        {
            new object?[] { null },
            new object?[] { 1 },
            new object?[] { "Bogus" },
            new object?[] { DateTime.Now },
            new object?[] { new { Id = 2, Name = "Object2" } }
        };

        public IEnumerator<object[]> GetEnumerator() => this._data.GetEnumerator();

        IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();
    }
}
