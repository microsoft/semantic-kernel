// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;

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

        this.TextEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());
    }

    /// <summary>
    /// Gets the text embedding generation service
    /// </summary>
    public ITextEmbeddingGenerationService TextEmbeddingGenerationService { get; }
}
