// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for the ServiceCollectionExtensions class.
/// </summary>
public class ServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection;

    public ServiceCollectionExtensionsTests()
    {
        this._serviceCollection = new ServiceCollection();
    }

    [Obsolete("The VolatileVectorStore is obsolete so this test is as well.")]
    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Act.
        this._serviceCollection.AddVolatileVectorStore();

        // Assert.
        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<VolatileVectorStore>(vectorStore);
    }
}
