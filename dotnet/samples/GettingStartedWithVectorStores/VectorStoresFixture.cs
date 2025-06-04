// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;

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

        this.EmbeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);
    }

    /// <summary>
    /// Gets the text embedding generation service
    /// </summary>
    public IEmbeddingGenerator<string, Embedding<float>> EmbeddingGenerator { get; }
}
