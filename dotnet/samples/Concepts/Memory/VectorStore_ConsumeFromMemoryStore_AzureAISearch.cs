// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Azure;
using Azure.Search.Documents.Indexes;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
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
public class VectorStore_ConsumeFromMemoryStore_AzureAISearch(ITestOutputHelper output) : BaseTest(output), IClassFixture<VectorStoreQdrantContainerFixture>
{
    private const int VectorSize = 1536;
    private readonly static JsonSerializerOptions s_consoleFormatting = new() { WriteIndented = true };

    [Fact]
    public async Task ConsumeExampleAsync()
    {
        // Construct a VectorStore.
        var vectorStore = new AzureAISearchVectorStore(new SearchIndexClient(
            new Uri(TestConfiguration.AzureAISearch.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureAISearch.ApiKey)));

        // Use the VectorStore abstraction to connect to an existing collection which was previously created via the IMemoryStore abstraction
        var collection = vectorStore.GetCollection<string, VectorStoreRecord>("memorystorecollection");
        await collection.EnsureCollectionExistsAsync();

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
    /// <see cref="MemoryRecord"/> objects as created by <c>AzureAISearchMemoryStore</c>.
    /// </summary>
    private sealed class VectorStoreRecord
    {
        [VectorStoreKey]
        public string Id { get; set; }

        [VectorStoreData]
        public string Description { get; set; }

        [VectorStoreData]
        public string Text { get; set; }

        [VectorStoreData]
        public bool IsReference { get; set; }

        [VectorStoreData]
        public string ExternalSourceName { get; set; }

        [VectorStoreData]
        public string AdditionalMetadata { get; set; }

        [VectorStoreVector(VectorSize)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
