// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Data;

/// <summary>
/// Integration tests for using <see cref="VolatileVectorStore"/> with <see cref="ITextSearch"/>.
/// </summary>
public class VolatileVectorStoreTextSearchTests : BaseVectorStoreTextSearchTests
{
    /// <inheritdoc/>
    public async override Task<ITextSearch> CreateTextSearchAsync()
    {
        if (this.VectorStore is null)
        {
            OpenAIConfiguration? openAIConfiguration = this.Configuration.GetSection("OpenAIEmbeddings").Get<OpenAIConfiguration>();
            Assert.NotNull(openAIConfiguration);
            Assert.NotEmpty(openAIConfiguration.ModelId);
            Assert.NotEmpty(openAIConfiguration.ApiKey);
            this.EmbeddingGenerator = new OpenAITextEmbeddingGenerationService(openAIConfiguration.ModelId, openAIConfiguration.ApiKey);

            // Delegate which will create a record.
            static DataModel CreateRecord(int index, string text, ReadOnlyMemory<float> embedding)
            {
                var guid = Guid.NewGuid();
                return new()
                {
                    Key = guid,
                    Text = text,
                    Link = $"noop://{guid}",
                    Tag = index % 2 == 0 ? "Even" : "Odd",
                    Embedding = embedding
                };
            }

            this.VectorStore = new VolatileVectorStore();
            await AddRecordsAsync<Guid, DataModel>(this.VectorStore, "records", this.EmbeddingGenerator, CreateRecord);
        }

        var vectorSearch = this.VectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        return new VectorStoreTextSearch<DataModel>(vectorSearch, this.EmbeddingGenerator!, stringMapper, resultMapper);
    }

    /// <inheritdoc/>
    public override string GetQuery() => "What is the Semantic Kernel?";

    /// <inheritdoc/>
    public override TextSearchFilter GetTextSearchFilter() => new TextSearchFilter().Equality("Tag", "Even");

    /// <inheritdoc/>
    public override bool VerifySearchResults(object[] results, string query, TextSearchFilter? filter = null)
    {
        Assert.NotNull(results);
        Assert.NotEmpty(results);
        Assert.Equal(4, results.Length);
        foreach (var result in results)
        {
            Assert.NotNull(result);
            Assert.IsType<DataModel>(result);
        }

        return true;
    }
}
