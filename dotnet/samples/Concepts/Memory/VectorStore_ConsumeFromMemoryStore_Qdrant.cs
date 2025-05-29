// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Qdrant.Client;

namespace Memory;

/// <summary>
/// An example showing how use the VectorStore abstractions to consume data from a Qdrant data store,
/// that was created using the MemoryStore abstractions.
/// </summary>
/// <remarks>
/// The IMemoryStore abstraction has limitations that constrain its use in many scenarios
/// e.g. it only supports a single fixed schema and does not allow search filtering.
/// To provide more flexibility, the Vector Store abstraction has been introduced.
///
/// To run this sample, you need a local instance of Docker running, since the associated fixture
/// will try and start a Qdrant container in the local docker instance to run against.
/// </remarks>
public class VectorStore_ConsumeFromMemoryStore_Qdrant(ITestOutputHelper output, VectorStoreQdrantContainerFixture qdrantFixture) : BaseTest(output), IClassFixture<VectorStoreQdrantContainerFixture>
{
    private const int VectorSize = 1536;
    private readonly static JsonSerializerOptions s_consoleFormatting = new() { WriteIndented = true };

    [Fact]
    public async Task ConsumeExampleAsync()
    {
        // Setup the supporting infra and embedding generation.
        await qdrantFixture.ManualInitializeAsync();

        // Construct a VectorStore.
        var vectorStore = new QdrantVectorStore(new QdrantClient("localhost"), ownsClient: true);

        // Use the VectorStore abstraction to connect to an existing collection which was previously created via the IMemoryStore abstraction
        var collection = vectorStore.GetCollection<Guid, VectorStoreRecord>("memorystorecollection");
        await collection.EnsureCollectionExistsAsync();

        // Show that the data can be read using the VectorStore abstraction.
        var record1 = await collection.GetAsync(new Guid("11111111-1111-1111-1111-111111111111"));
        var record2 = await collection.GetAsync(new Guid("22222222-2222-2222-2222-222222222222"));
        var record3 = await collection.GetAsync(new Guid("33333333-3333-3333-3333-333333333333"), new() { IncludeVectors = true });

        Console.WriteLine($"Record 1: {JsonSerializer.Serialize(record1, s_consoleFormatting)}");
        Console.WriteLine($"Record 2: {JsonSerializer.Serialize(record2, s_consoleFormatting)}");
        Console.WriteLine($"Record 3: {JsonSerializer.Serialize(record3, s_consoleFormatting)}");
    }

    /// <summary>
    /// A data model with Vector Store attributes that matches the storage representation of
    /// <see cref="MemoryRecord"/> objects as created by <c>QdrantMemoryStore</c>.
    /// </summary>
    private sealed class VectorStoreRecord
    {
        [VectorStoreKey]
        public Guid Key { get; set; }

        [VectorStoreData(StorageName = "id")]
        public string Id { get; set; }

        [VectorStoreData(StorageName = "description")]
        public string Description { get; set; }

        [VectorStoreData(StorageName = "text")]
        public string Text { get; set; }

        [VectorStoreData(StorageName = "is_reference")]
        public bool IsReference { get; set; }

        [VectorStoreData(StorageName = "external_source_name")]
        public string ExternalSourceName { get; set; }

        [VectorStoreData(StorageName = "additional_metadata")]
        public string AdditionalMetadata { get; set; }

        [VectorStoreVector(VectorSize)]
        public ReadOnlyMemory<float> Embedding { get; set; }
    }
}
