// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;
using MongoDB.Driver;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBMongoDBKernelBuilderExtensions"/> class.
/// </summary>
public sealed class AzureCosmosDBMongoDBKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<IMongoDatabase>(Mock.Of<IMongoDatabase>());

        // Act
        this._kernelBuilder.AddAzureCosmosDBMongoDBVectorStore();

        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBMongoDBVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreWithConnectionStringRegistersClass()
    {
        // Act
        this._kernelBuilder.AddAzureCosmosDBMongoDBVectorStore("mongodb://localhost:27017", "mydb");

        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBMongoDBVectorStore>(vectorStore);

        var database = (IMongoDatabase)vectorStore.GetType().GetField("_mongoDatabase", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(vectorStore)!;
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, database.Client.Settings.ApplicationName);
    }
}
