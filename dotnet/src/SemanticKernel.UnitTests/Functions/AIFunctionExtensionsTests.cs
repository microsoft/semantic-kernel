// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Xunit;

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

        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<object?>(null);
        }
    }
}
