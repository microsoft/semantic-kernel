// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Redis;
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

    [Fact]
    public void AddRedisHashSetVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange.
        this._kernelBuilder.Services.AddSingleton<IDatabase>(Mock.Of<IDatabase>());

        // Act.
        this._kernelBuilder.AddRedisHashSetVectorStoreRecordCollection<TestRecord>("testCollection");

        // Assert.
        this.AssertHashSetVectorStoreRecordCollectionCreated<TestRecord>();
    }

    [Fact]
    public void AddRedisJsonVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange.
        this._kernelBuilder.Services.AddSingleton<IDatabase>(Mock.Of<IDatabase>());

        // Act.
        this._kernelBuilder.AddRedisJsonVectorStoreRecordCollection<TestRecord>("testCollection");

        // Assert.
        this.AssertJsonVectorStoreRecordCollectionCreated<TestRecord>();
    }

    private void AssertVectorStoreCreated()
    {
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<RedisVectorStore>(vectorStore);
    }

    private void AssertHashSetVectorStoreRecordCollectionCreated<TRecord>() where TRecord : notnull
    {
        var kernel = this._kernelBuilder.Build();
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<string, TRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<RedisHashSetVectorStoreRecordCollection<string, TRecord>>(collection);
    }

    private void AssertJsonVectorStoreRecordCollectionCreated<TRecord>() where TRecord : notnull
    {
        var kernel = this._kernelBuilder.Build();
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<string, TRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<RedisJsonVectorStoreRecordCollection<string, TRecord>>(collection);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = string.Empty;
    }
}
