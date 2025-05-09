// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;

namespace GettingStartedWithVectorStores;

/// <summary>
/// Fixture containing common setup logic for the samples.
/// </summary>
public class VectorStoresFixture
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoresFixture"/> class.
    /// </summary>
    public VectorStoresFixture()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
            .Build();
        TestConfiguration.Initialize(configRoot);

        this.EmbeddingGenerator = new AzureOpenAIEmbeddingGenerator(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());
    }

    /// <summary>
    /// Gets the text embedding generation service
    /// </summary>
    public IEmbeddingGenerator<string, Embedding<float>> EmbeddingGenerator { get; }
}
