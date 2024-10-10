﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using static SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch.AzureAISearchVectorStoreFixture;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Integration tests for using <see cref="AzureAISearchVectorStore"/> with <see cref="ITextSearch"/>.
/// </summary>
[Collection("AzureAISearchVectorStoreCollection")]
public class AzureAISearchTextSearchTests(AzureAISearchVectorStoreFixture fixture) : BaseVectorStoreTextSearchTests
{
    // If null, all tests will be enabled
    private const string SkipReason = "Requires Azure AI Search Service instance up and running";

    [Fact(Skip = SkipReason)]
    public override async Task CanSearchAsync()
    {
        await base.CanSearchAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task CanGetTextSearchResultsAsync()
    {
        await base.CanGetTextSearchResultsAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task CanGetSearchResultsAsync()
    {
        await base.CanGetSearchResultsAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task UsingTextSearchWithAFilterAsync()
    {
        await base.UsingTextSearchWithAFilterAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task FunctionCallingUsingCreateWithSearchAsync()
    {
        await base.FunctionCallingUsingCreateWithSearchAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task FunctionCallingUsingCreateWithGetSearchResultsAsync()
    {
        await base.FunctionCallingUsingCreateWithGetSearchResultsAsync();
    }

    [Fact(Skip = SkipReason)]
    public override async Task FunctionCallingUsingGetTextSearchResultsAsync()
    {
        await base.FunctionCallingUsingGetTextSearchResultsAsync();
    }

    /// <inheritdoc/>
    public override Task<ITextSearch> CreateTextSearchAsync()
    {
        if (this.VectorStore is null)
        {
            AzureOpenAIConfiguration? azureOpenAIConfiguration = this.Configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
            Assert.NotNull(azureOpenAIConfiguration);
            Assert.NotEmpty(azureOpenAIConfiguration.DeploymentName);
            Assert.NotEmpty(azureOpenAIConfiguration.Endpoint);
            this.EmbeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(
                azureOpenAIConfiguration.DeploymentName,
                azureOpenAIConfiguration.Endpoint,
                new AzureCliCredential());

            this.VectorStore = new AzureAISearchVectorStore(fixture.SearchIndexClient);
        }

        var vectorSearch = this.VectorStore.GetCollection<string, Hotel>(fixture.TestIndexName);
        var stringMapper = new HotelTextSearchStringMapper();
        var resultMapper = new HotelTextSearchResultMapper();

        var result = new VectorStoreTextSearch<Hotel>(vectorSearch, this.EmbeddingGenerator!, stringMapper, resultMapper);
        return Task.FromResult<ITextSearch>(result);
    }

    /// <inheritdoc/>
    public override string GetQuery() => "Find a great hotel";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("Rating", 3.6);

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(filter is null ? 4 : 2, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            Assert.IsType<Hotel>(result);
        }

        return true;
    }

    /// <summary>
    /// String mapper which converts a Hotel to a string.
    /// </summary>
    protected sealed class HotelTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is Hotel hotel)
            {
                return $"{hotel.HotelName} {hotel.Description}";
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Result mapper which converts a Hotel to a TextSearchResult.
    /// </summary>
    protected sealed class HotelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is Hotel hotel)
            {
                return new TextSearchResult(value: hotel.Description) { Name = hotel.HotelName, Link = $"id://{hotel.HotelId}" };
            }
            throw new ArgumentException("Invalid result type.");
        }
    }
}
