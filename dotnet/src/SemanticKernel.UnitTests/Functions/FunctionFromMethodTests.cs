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
}
