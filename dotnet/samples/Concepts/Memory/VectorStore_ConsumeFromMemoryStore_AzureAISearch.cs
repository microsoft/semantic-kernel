// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Azure;
using Azure.Identity;
using Azure.Search.Documents.Indexes;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Memory;

namespace Memory;

/// <summary>
/// An example showing how use the VectorStore abstractions to consume data from an Azure AI Search data store,
/// that was created using the MemoryStore abstractions.
/// </summary>
/// <remarks>
/// The IMemoryStore abstraction has limitations that constrain its use in many scenarios
/// e.g. it only supports a single fixed schema and does not allow search filtering.
/// To provide more flexibility, the Vector Store abstraction has been introduced.
///
/// To run this sample, you need an instance of Azure AI Search available and configured.
/// dotnet user-secrets set "AzureAISearch:Endpoint" "https://myazureaisearchinstance.search.windows.net"
/// dotnet user-secrets set "AzureAISearch:ApiKey" "samplesecret"
/// </remarks>
[Obsolete("The IMemoryStore abstraction is being obsoleted")]
public class VectorStore_ConsumeFromMemoryStore_AzureAISearch(ITestOutputHelper output, VectorStoreQdrantContainerFixture qdrantFixture) : BaseTest(output), IClassFixture<VectorStoreQdrantContainerFixture>
{
    private const int VectorSize = 1536;
    private const string MemoryStoreCollectionName = "memorystorecollection";
    private readonly static JsonSerializerOptions s_consoleFormatting = new() { WriteIndented = true };

    [Fact]
    public async Task ConsumeExampleAsync()
    {
        // Setup the supporting infra and embedding generation.
        await qdrantFixture.ManualInitializeAsync();
        var textEmbeddingService = new AzureOpenAITextEmbeddingGenerationService(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            new AzureCliCredential());

        // Construct a legacy MemoryStore.
        var memoryStore = new AzureAISearchMemoryStore(
            TestConfiguration.AzureAISearch.Endpoint,
            TestConfiguration.AzureAISearch.ApiKey);

        // Construct a VectorStore.
        var vectorStore = new AzureAISearchVectorStore(new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey)));

        // Build a collection with sample data using the MemoryStore abstraction.
        await VectorStore_ConsumeFromMemoryStore_Common.CreateCollectionAndAddSampleDataAsync(
            memoryStore,
            MemoryStoreCollectionName,
            textEmbeddingService);

        // Connect to the same collection using the VectorStore abstraction.
        var collection = vectorStore.GetCollection<string, VectorStoreRecord>(MemoryStoreCollectionName);
        await collection.CreateCollectionIfNotExistsAsync();

        // Show that the data can be read using the VectorStore abstraction.
        // Note that AzureAISearchMemoryStore converts all keys to base64
        // strings on upload so we need to encode the ids here before doing a get.
        var record1 = await collection.GetAsync(Convert.ToBase64String(Encoding.UTF8.GetBytes("11111111-1111-1111-1111-111111111111")));
        var record2 = await collection.GetAsync(Convert.ToBase64String(Encoding.UTF8.GetBytes("22222222-2222-2222-2222-222222222222")));
        var record3 = await collection.GetAsync(Convert.ToBase64String(Encoding.UTF8.GetBytes("33333333-3333-3333-3333-333333333333")), new() { IncludeVectors = true });

        Console.WriteLine($"Record 1: {JsonSerializer.Serialize(record1, s_consoleFormatting)}");
        Console.WriteLine($"Record 2: {JsonSerializer.Serialize(record2, s_consoleFormatting)}");
        Console.WriteLine($"Record 3: {JsonSerializer.Serialize(record3, s_consoleFormatting)}");
    }

    /// <summary>
    /// A data model with Vector Store attributes that matches the storage representation of
    /// <see cref="MemoryRecord"/> objects as created by <see cref="AzureAISearchMemoryStore"/>.
    /// </summary>
    private sealed class VectorStoreRecord
    {
        [VectorStoreRecordKey]
        public string Id { get; set; }

        [VectorStoreRecordData]
        public string Description { get; set; }

        [VectorStoreRecordData]
        public string Text { get; set; }

        [VectorStoreRecordData]
        public bool IsReference { get; set; }

        [VectorStoreRecordData]
        public string ExternalSourceName { get; set; }

        [VectorStoreRecordData]
        public string AdditionalMetadata { get; set; }

        [VectorStoreRecordVector(VectorSize)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
