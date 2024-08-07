// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Data;
using Moq;
using StackExchange.Redis;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Tests for the <see cref="RedisKernelBuilderExtensions"/> class.
/// </summary>
public class RedisKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder;

    public RedisKernelBuilderExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange.
        this._kernelBuilder.Services.AddSingleton<IDatabase>(Mock.Of<IDatabase>());

        // Act.
        this._kernelBuilder.AddRedisVectorStore();

        // Assert.
        this.AssertVectorStoreCreated();
    }

    private void AssertVectorStoreCreated()
    {
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<RedisVectorStore>(vectorStore);
    }
}
