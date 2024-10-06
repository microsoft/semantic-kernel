// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
<<<<<<< Updated upstream
using Microsoft.SemanticKernel;
=======
<<<<<<< HEAD
using Microsoft.SemanticKernel;
=======
<<<<<<< HEAD
using Microsoft.SemanticKernel;
=======
>>>>>>> 46c3c89f5c5dbc355794ac231b509e142f4fb770
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for the <see cref="ServiceCollectionExtensions"/> class.
/// </summary>
public class ServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection;

    public ServiceCollectionExtensionsTests()
    {
        this._serviceCollection = new ServiceCollection();
    }

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
