// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="VectorStoreRecordTextSearch{TRecord}"/>.
/// </summary>
public class VectorStore_TextSearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="VectorStoreRecordTextSearch{TRecord}"/> and use it to perform a text search
    /// on top of the <see cref="VolatileVectorStore"/>.
    /// </summary>
    [Fact]
    public async Task UsingVolatileVectorStoreRecordTextSearchAsync()
    {
        var volatileStore = new VolatileVectorStore();
        var recordCollection = volatileStore.GetCollection<string, DataModel<string>>("MyData");

        // Create an ITextSearch instance using Bing search
        /*
        var textSearch = new VectorStoreRecordTextSearch<DataModel<string>>(
            vectorSearch: recordCollection,
            textEmbeddingGeneration: );
        */

        var query = "What is the Semantic Kernel?";
    }

    private sealed class DataModel<TKey>
    {
        [VectorStoreRecordKey]
        public required TKey Key { get; set; }

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector { get; set; }
    }
}
