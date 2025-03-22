// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using VectorDataSpecificationTests.Support;

namespace AzureAISearchIntegrationTests.Support;

internal sealed class AzureAISearchTestStore : TestStore
{
    public static AzureAISearchTestStore Instance { get; } = new();

    private SearchIndexClient? _client;
    private AzureAISearchVectorStore? _defaultVectorStore;

    public SearchIndexClient Client
        => this._client ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public AzureAISearchVectorStore GetVectorStore(AzureAISearchVectorStoreOptions options)
        => new(this.Client, options);

    private AzureAISearchTestStore()
    {
    }

    protected override Task StartAsync()
    {
        (string? serviceUrl, string? apiKey) = (AzureAISearchTestEnvironment.ServiceUrl, AzureAISearchTestEnvironment.ApiKey);

        if (string.IsNullOrWhiteSpace(serviceUrl) || string.IsNullOrWhiteSpace(apiKey))
        {
            throw new InvalidOperationException("Service URL and API key are not configured, set AzureAISearch:ServiceUrl and AzureAISearch:ApiKey");
        }

        this._client = new SearchIndexClient(new Uri(serviceUrl), new AzureKeyCredential(apiKey));
        this._defaultVectorStore = new(this._client);

        return Task.CompletedTask;
    }

    public override async Task WaitForDataAsync<TKey, TRecord>(
        IVectorStoreRecordCollection<TKey, TRecord> collection,
        int recordCount,
        Expression<Func<TRecord, bool>>? filter = null)
    {
        await base.WaitForDataAsync(collection, recordCount, filter);

        // There seems to be some asynchronicity/race condition specific to Azure AI Search which isn't taken care
        // of by the generic retry loop in the base implementation.
        // TODO: Investigate this and remove
        await Task.Delay(TimeSpan.FromMilliseconds(1000));
    }
}
