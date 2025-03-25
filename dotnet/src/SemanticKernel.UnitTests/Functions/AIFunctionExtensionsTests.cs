// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.Extensions.AI;
using Xunit;
using Microsoft.SemanticKernel;

namespace SemanticKernel.UnitTests.Functions;

public class AIFunctionExtensionsTests
{
    [Fact]
    public void ItShouldCreateKernelFunctionFromAIFunction()
    {
        // Arrange
        AIFunction aiFunction = new TestAIFunction("TestFunction");

        // Act
        KernelFunction kernelFunction = aiFunction.AsKernelFunction();

        // Assert
        Assert.Equal("TestFunction", kernelFunction.Name);
    }

    private sealed class TestAIFunction(string name) : AIFunction
    {
        public override string Name => name;

        protected override Task<object?> InvokeCoreAsync(IEnumerable<KeyValuePair<string, object?>> arguments, CancellationToken cancellationToken)
        {
            return Task.FromResult<object?>(null);
        }
    }
}
