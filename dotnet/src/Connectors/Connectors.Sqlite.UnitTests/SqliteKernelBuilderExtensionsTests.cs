// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteKernelBuilderExtensions"/> class.
/// </summary>
public sealed class SqliteKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<SqliteConnection>(Mock.Of<SqliteConnection>());

        // Act
        this._kernelBuilder.AddSqliteVectorStore();

        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<SqliteVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreWithSqliteConnectionRegistersClass()
    {
        // Act
        this._kernelBuilder.AddSqliteVectorStore(Mock.Of<SqliteConnection>());

        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<SqliteVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithStringKeyRegistersClass()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<SqliteConnection>(Mock.Of<SqliteConnection>());

        // Act
        this._kernelBuilder.AddSqliteVectorStoreRecordCollection<string, TestRecord>("testcollection");

        var kernel = this._kernelBuilder.Build();

        // Assert
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithNumericKeyRegistersClass()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<SqliteConnection>(Mock.Of<SqliteConnection>());

        // Act
        this._kernelBuilder.AddSqliteVectorStoreRecordCollection<ulong, TestRecord>("testcollection");

        var kernel = this._kernelBuilder.Build();

        // Assert
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithStringKeyAndSqliteConnectionRegistersClass()
    {
        // Act
        this._kernelBuilder.AddSqliteVectorStoreRecordCollection<string, TestRecord>("testcollection", Mock.Of<SqliteConnection>());

        var kernel = this._kernelBuilder.Build();

        // Assert
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithNumericKeyAndSqliteConnectionRegistersClass()
    {
        // Act
        this._kernelBuilder.AddSqliteVectorStoreRecordCollection<ulong, TestRecord>("testcollection", Mock.Of<SqliteConnection>());

        var kernel = this._kernelBuilder.Build();

        // Assert
        var collection = kernel.Services.GetRequiredService<IVectorStoreRecordCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = kernel.Services.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
    }

    #region private

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = string.Empty;
    }

    #endregion
}
