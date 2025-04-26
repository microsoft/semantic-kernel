// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.IntegrationTests.Data;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.InMemory;

/// <summary>
/// Integration tests for using <see cref="InMemoryVectorStore"/> with <see cref="ITextSearch"/>.
/// </summary>
public class InMemoryVectorStoreTextSearchTests : BaseVectorStoreTextSearchTests
{
    /// <inheritdoc/>
    public async override Task<ITextSearch> CreateTextSearchAsync()
    {
        if (this.VectorStore is null)
        {
            OpenAIConfiguration? openAIConfiguration = this.Configuration.GetSection("OpenAIEmbeddings").Get<OpenAIConfiguration>();
            Assert.NotNull(openAIConfiguration);
            Assert.NotNull(openAIConfiguration.ModelId);
            Assert.NotNull(openAIConfiguration.ApiKey);
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

            this.VectorStore = new InMemoryVectorStore();
            await AddRecordsAsync<Guid, DataModel>(this.VectorStore, "records", this.EmbeddingGenerator, CreateRecord);
        }

        var vectorSearch = this.VectorStore.GetCollection<Guid, DataModel>("records");
        var stringMapper = new DataModelTextSearchStringMapper();
        var resultMapper = new DataModelTextSearchResultMapper();

        // TODO: Once OpenAITextEmbeddingGenerationService implements MEAI's IEmbeddingGenerator (#10811), configure it with the InMemoryVectorStore above instead of passing it here.
#pragma warning disable CS0618 // VectorStoreTextSearch with ITextEmbeddingGenerationService is obsolete
        return new VectorStoreTextSearch<DataModel>(vectorSearch, this.EmbeddingGenerator!, stringMapper, resultMapper);
#pragma warning restore CS0618
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
