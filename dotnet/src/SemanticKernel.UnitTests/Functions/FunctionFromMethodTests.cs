// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
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
        StreamingKernelContent? lastChunk = null;
        // Act
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingKernelContent>(kernel))
        {
            chunkCount++;
            lastChunk = chunk;
        }

        // Assert
        Assert.Equal(1, chunkCount);
        Assert.NotNull(lastChunk);
        Assert.IsAssignableFrom<StreamingKernelContent>(lastChunk);
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
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingKernelContent>(kernel))
        {
        }

        // Assert
        Assert.True(invokingCalled);
        Assert.False(invokedCalled);
    }

    [Fact]
    public async Task InvokeStreamingAsyncInvokingCancelingShouldThrowAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var sut = KernelFunctionFactory.CreateFromMethod(() => "any");

        bool invokingCalled = false;
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invokingCalled = true;
            e.Cancel = true;
        };

        // Act
        IAsyncEnumerable<StreamingKernelContent> enumerable = sut.InvokeStreamingAsync<StreamingKernelContent>(kernel);
        IAsyncEnumerator<StreamingKernelContent> enumerator = enumerable.GetAsyncEnumerator();
        Assert.False(invokingCalled);
        var e = await Assert.ThrowsAsync<KernelFunctionCanceledException>(async () => await enumerator.MoveNextAsync());

        // Assert
        Assert.True(invokingCalled);
        Assert.Same(sut, e.Function);
        Assert.Same(kernel, e.Kernel);
        Assert.Empty(e.Arguments);
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
        await foreach (var chunk in sut.InvokeStreamingAsync<StreamingKernelContent>(kernel))
        {
            chunkCount++;
        }

        // Assert
        Assert.Equal(1, chunkCount);
    }
}
