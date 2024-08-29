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
/// Unit tests for <see cref="AzureCosmosDBNoSQLKernelBuilderExtensions"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLKernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<Database>(Mock.Of<Database>());

        // Act
        this._kernelBuilder.AddAzureCosmosDBNoSQLVectorStore();

        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBNoSQLVectorStore>(vectorStore);
    }
}
