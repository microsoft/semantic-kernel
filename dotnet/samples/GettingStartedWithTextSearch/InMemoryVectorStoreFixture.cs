// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace GettingStartedWithTextSearch;

/// <summary>
/// Helper class for setting up and tearing down a <see cref="InMemoryVectorStore"/> for testing purposes.
/// </summary>
public class InMemoryVectorStoreFixture : IAsyncLifetime
{
    public ITextEmbeddingGenerationService TextEmbeddingGenerationService { get; private set; }

    public InMemoryVectorStore InMemoryVectorStore { get; private set; }

    public IVectorStoreRecordCollection<Guid, DataModel> VectorStoreRecordCollection { get; private set; }

    public string CollectionName => "records";

    /// <summary>
    /// Initializes a new instance of the <see cref="InMemoryVectorStoreFixture"/> class.
    /// </summary>
    public InMemoryVectorStoreFixture()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets(Assembly.GetExecutingAssembly())
            .Build();
        TestConfiguration.Initialize(configRoot);

        // Create an InMemory vector store.
        this.InMemoryVectorStore = new InMemoryVectorStore();

        // Create an embedding generation service.
        this.TextEmbeddingGenerationService = new OpenAITextEmbeddingGenerationService(
                TestConfiguration.OpenAI.EmbeddingModelId,
                TestConfiguration.OpenAI.ApiKey);
    }

    /// <inheritdoc/>
    public async Task DisposeAsync()
    {
        await this.VectorStoreRecordCollection.DeleteCollectionAsync().ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task InitializeAsync()
    {
        this.VectorStoreRecordCollection = await InitializeRecordCollectionAsync();
    }

    #region private
    /// <summary>
    /// Initialize a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with a list of strings.
    /// </summary>
    private async Task<IVectorStoreRecordCollection<Guid, DataModel>> InitializeRecordCollectionAsync()
    {
        // Delegate which will create a record.
        static DataModel CreateRecord(int index, string text, ReadOnlyMemory<float> embedding)
        {
            var guid = Guid.NewGuid();
            return new()
            {
                Key = guid,
                Text = text,
                Link = $"guid://{guid}",
                Tag = index % 2 == 0 ? "Even" : "Odd",
                Embedding = embedding
            };
        }

        // Create a record collection from a list of strings using the provided delegate.
        string[] lines =
        [
            "Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase. It serves as an efficient middleware that enables rapid delivery of enterprise-grade solutions.",
            "Semantic Kernel is a new AI SDK, and a simple and yet powerful programming model that lets you add large language capabilities to your app in just a matter of minutes. It uses natural language prompting to create and execute semantic kernel AI tasks across multiple languages and platforms.",
            "In this guide, you learned how to quickly get started with Semantic Kernel by building a simple AI agent that can interact with an AI service and run your code. To see more examples and learn how to build more complex AI agents, check out our in-depth samples.",
            "The Semantic Kernel extension for Visual Studio Code makes it easy to design and test semantic functions.The extension provides an interface for designing semantic functions and allows you to test them with the push of a button with your existing models and data.",
            "The kernel is the central component of Semantic Kernel.At its simplest, the kernel is a Dependency Injection container that manages all of the services and plugins necessary to run your AI application.",
            "Semantic Kernel (SK) is a lightweight SDK that lets you mix conventional programming languages, like C# and Python, with the latest in Large Language Model (LLM) AI “prompts” with prompt templating, chaining, and planning capabilities.",
            "Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your C#, Python, or Java codebase. It serves as an efficient middleware that enables rapid delivery of enterprise-grade solutions. Enterprise ready.",
            "With Semantic Kernel, you can easily build agents that can call your existing code.This power lets you automate your business processes with models from OpenAI, Azure OpenAI, Hugging Face, and more! We often get asked though, “How do I architect my solution?” and “How does it actually work?”"

        ];
        var vectorizedSearch = await CreateCollectionFromListAsync<Guid, DataModel>(lines, CreateRecord);
        return vectorizedSearch;
    }

    /// <summary>
    /// Delegate to create a record.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    internal delegate TRecord CreateRecord<TKey, TRecord>(int index, string text, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Create a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Creating an instance of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="entries">A list of strings.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    private async Task<IVectorStoreRecordCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
        string[] entries,
        CreateRecord<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : notnull
    {
        // Get and create collection if it doesn't exist.
        var collection = this.InMemoryVectorStore.GetCollection<TKey, TRecord>(this.CollectionName);
        await collection.CreateCollectionIfNotExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = entries.Select((entry, i) => Task.Run(async () =>
        {
            var record = createRecord(i, entry, await this.TextEmbeddingGenerationService.GenerateEmbeddingAsync(entry).ConfigureAwait(false));
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }

    /// <summary>
    /// Sample model class that represents a record entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
    public sealed class DataModel
    {
        [VectorStoreRecordKey]
        [TextSearchResultName]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        [TextSearchResultValue]
        public string Text { get; init; }

        [VectorStoreRecordData]
        [TextSearchResultLink]
        public string Link { get; init; }

        [VectorStoreRecordData(IsIndexed = true)]
        public required string Tag { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
    #endregion
}
