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
        var resultValueInvokeSignature2 = await testFunction.InvokeAsync<object>(kernel);

        Assert.Equal(expectedValue, resultValueInvokeSignature2);
    }

    public class ComplexObjectTestData : IEnumerable<object[]>
    {
        private readonly List<object?[]> _data =
        [
            [null],
            [1],
            ["Bogus"],
            [DateTime.Now],
            [new { Id = 2, Name = "Object2" }]
        ];

        public IEnumerator<object[]> GetEnumerator() => this._data.GetEnumerator();

        IEnumerator IEnumerable.GetEnumerator() => this.GetEnumerator();
    }
}
