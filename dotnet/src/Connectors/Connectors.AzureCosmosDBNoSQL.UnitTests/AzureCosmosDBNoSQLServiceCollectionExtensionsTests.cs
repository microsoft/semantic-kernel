// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._serviceCollection.AddSingleton<Database>(Mock.Of<Database>());

        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBNoSQLVectorStore>(vectorStore);
    }
}
