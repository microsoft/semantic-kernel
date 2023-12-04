// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Events;
using Xunit;

// ReSharper disable StringLiteralTypo

namespace SemanticKernel.UnitTests.Functions;

public class FunctionFromMethodTests
{
    [Fact]
    public async Task InvokeStreamingAsyncShouldReturnOneChunkFromNonStreamingMethodAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var nativeContent = "Full content result";
        var sut = KernelFunctionFactory.CreateFromMethod(() => nativeContent);

        var chunkCount = 0;
        StreamingContentBase? lastChunk = null;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContentBase>(kernel))
        {
            chunkCount++;
            lastChunk = chunk;
        }

        // Assert
        Assert.Equal(1, chunkCount);
        Assert.NotNull(lastChunk);
        Assert.IsAssignableFrom<StreamingContentBase>(lastChunk);
        Assert.IsType<StreamingMethodContent>(lastChunk);

        var methodContent = lastChunk as StreamingMethodContent;
        Assert.Equal(nativeContent, methodContent!.Content);
    }

    [Fact]
    public async Task InvokeStreamingAsyncOnlySupportsInvokingEventAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var sut = KernelFunctionFactory.CreateFromMethod(() => "any");

        var invokedCalled = false;
        var invokingCalled = false;

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invokingCalled = true;
        };

        // Invoked is not supported for streaming...
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invokedCalled = true;
        };

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContentBase>(kernel))
        {
        }

        // Assert
        Assert.True(invokingCalled);
        Assert.False(invokedCalled);
    }

    [Fact]
    public async Task InvokeStreamingAsyncInvokingCancellingShouldRenderNoChunksAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var sut = KernelFunctionFactory.CreateFromMethod(() => "any");

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Cancel = true;
        };
        var chunkCount = 0;

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContentBase>(kernel))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(0, chunkCount);
    }

    [Fact]
    public async Task InvokeStreamingAsyncUsingInvokedEventHasNoEffectAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var sut = KernelFunctionFactory.CreateFromMethod(() => "any");

        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            // This will have no effect on streaming
            e.Cancel = true;
        };

        var chunkCount = 0;

        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingContentBase>(kernel))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(1, chunkCount);
    }
}
