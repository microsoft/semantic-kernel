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

        // Act
        var chunkCount = 0;
        StreamingKernelContent? lastChunk = null;
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
    public async Task InvokeStreamingAsyncShouldPropagateMetadataFromNonStreamingMethodAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var nativeContent = "Full content result";
        var sut = KernelFunctionFactory.CreateFromMethod((KernelFunction func) =>
        {
            return new FunctionResult(func, nativeContent, metadata: new Dictionary<string, object?>()
            {
                { "key1", "value1" },
                { "key2", "value2" },
            });
        });

        // Act
        var chunkCount = 0;
        StreamingKernelContent? lastChunk = null;
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

        Assert.NotNull(methodContent.Metadata);
        Assert.Equal(2, methodContent.Metadata.Count);
        Assert.Equal("value1", methodContent.Metadata["key1"]);
        Assert.Equal("value2", methodContent.Metadata["key2"]);
    }

    [Fact]
    public async Task InvokeStreamingAsyncOnlySupportsInvokingEventAsync()
    {
        // Arrange
        var kernel = new Kernel();
        var sut = KernelFunctionFactory.CreateFromMethod(() => "any");

        var invokedCalled = false;
        var invokingCalled = false;

#pragma warning disable CS0618 // Events are deprecated
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invokingCalled = true;
        };

        // Invoked is not supported for streaming...
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invokedCalled = true;
        };
#pragma warning restore CS0618 // Events are deprecated

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

#pragma warning disable CS0618 // Type or member is obsolete
        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invokingCalled = true;
            e.Cancel = true;
        };
#pragma warning restore CS0618 // Type or member is obsolete

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

#pragma warning disable CS0618 // Type or member is obsolete
        kernel.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            // This will have no effect on streaming
            e.Cancel = true;
        };
#pragma warning restore CS0618 // Type or member is obsolete

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
