

using System;
using System.Linq;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Connectors.AstraDB;
using Xunit;
using Xunit.Abstractions;


namespace SemanticKernel.IntegrationTests.Connectors.AstraDB;
public class AstraDBMemoryStoreTests
{
  private const string? SkipReason = "Astra Database is required for tests";
  public AstraDBMemoryStoreTests(ITestOutputHelper output)
  {
    this._astraDbMemoryStore = this.CreateMemoryStore();
    _output = output;
  }

  private readonly ITestOutputHelper _output;

  // public AstraDBMemoryStoreTests(ITestOutputHelper output)
  // {
  //   _output = output;
  // }


  [Fact(Skip = SkipReason)]
  public async Task ItCanCreateAndGetCollectionAsync()
  {
    // Arrange: Create a collection
    string collection = "vector_collection";
    await this._astraDbMemoryStore.CreateCollectionAsync(collection);

    var collectionNames = this._astraDbMemoryStore.GetCollectionsAsync();
    Assert.True(await collectionNames.ContainsAsync(collection));
  }
  [Fact(Skip = SkipReason)]
  public async Task ItCanCheckIfCollectionExistsAsync()
  {
    // Arrange: Create a collection
    string collection = "vector_search_collection";
    await this._astraDbMemoryStore.CreateCollectionAsync(collection);

    Assert.True(await this._astraDbMemoryStore.DoesCollectionExistAsync("vector_search_collection"));
    Assert.False(await this._astraDbMemoryStore.DoesCollectionExistAsync("non_vector_search_collection"));
  }
  [Fact(Skip = SkipReason)]
  public async Task ItCanDeleteCollectionAsync()
  {
    // Arrange: Create a collection
    string collection = "collection_to_delete";
    await this._astraDbMemoryStore.CreateCollectionAsync(collection);

    // Ensure the collection exists before deletion
    Assert.True(await this._astraDbMemoryStore.DoesCollectionExistAsync(collection));

    // Act: Delete the collection
    await this._astraDbMemoryStore.DeleteCollectionAsync(collection);

    // Assert: Ensure the collection no longer exists
    Assert.False(await this._astraDbMemoryStore.DoesCollectionExistAsync(collection));
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanUpsertRecordAsync()
  {
    // Arrange: Create a collection
    string collection = "test_collection";
    await this._astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecord = MemoryRecord.LocalRecord(
            id: "test_id",
            text: "test_text",
            description: "test_description",
            embedding: new float[] { 1, 2, 3, 4, 5 });

    var upsertedKey = await this._astraDbMemoryStore.UpsertAsync(collection, testRecord);

    Assert.Equal(testRecord.Metadata.Id, upsertedKey);
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanUpsertBatchRecordsAsync()
  {
    // Arrange: Create a collection
    string collection = "test_collection";
    await this._astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecords = new List<MemoryRecord>
        {
            MemoryRecord.LocalRecord(
                id: "batch_test_id_1",
                text: "batch_test_text_1",
                description: "batch_test_description_1",
                embedding: new float[] { 1, 2, 3, 4, 5 }),
            MemoryRecord.LocalRecord(
                id: "batch_test_id_2",
                text: "batch_test_text_2",
                description: "batch_test_description_2",
                embedding: new float[] { 6, 7, 8, 9, 10 }),
            MemoryRecord.LocalRecord(
                id: "batch_test_id_3",
                text: "batch_test_text_3",
                description: "batch_test_description_3",
                embedding: new float[] { 11, 12, 13, 14, 15 })
        };

    var upsertedKeys = new List<string>();

    await foreach (var key in this._astraDbMemoryStore.UpsertBatchAsync(collection, testRecords))
    {
      upsertedKeys.Add(key);
    }

    Assert.Equal(testRecords.Count, upsertedKeys.Count);

    foreach (var record in testRecords)
    {
      Assert.Contains(record.Metadata.Id, upsertedKeys);
    }
  }

  // [Fact(Skip = null)]
  // public async Task ItCanGetRecordAsync()
  // {
  //   // Arrange: Create a collection and insert a record
  //   string collection = "get_test_collection";
  //   await this._astraDbMemoryStore.CreateCollectionAsync(collection);

  //   var testRecord = MemoryRecord.LocalRecord(
  //       id: "test_id",
  //       text: "test_text",
  //       description: "test_description",
  //       embedding: new float[] { 1, 2, 3, 4, 5 });

  //   await this._astraDbMemoryStore.UpsertAsync(collection, testRecord);

  //   // Act: Get the record
  //   var fetchedRecord = await this._astraDbMemoryStore.GetAsync(collection, testRecord.Key);
  //   _output.WriteLine($"Retrieved Record: {fetchedRecord}");

  //   // Assert: Ensure the record was fetched correctly
  //   Assert.NotNull(fetchedRecord);
  //   // Assert.Equal(testRecord.Key, fetchedRecord.Key);
  //   // Assert.Equal(testRecord.Metadata.Id, fetchedRecord.Metadata.Id);
  //   // Assert.Equal(testRecord.Metadata.Text, fetchedRecord.Metadata.Text);
  //   // Assert.Equal(testRecord.Metadata.Description, fetchedRecord.Metadata.Description);
  //   // Assert.Equal(testRecord.Embedding, fetchedRecord.Embedding);
  // }

  // [Fact(Skip = SkipReason)]
  // public async Task GetAsync_ReturnsNullIfCollectionDoesNotExist()
  // {
  //   // Arrange: Use a non-existing collection name
  //   string collection = "non_existing_collection";
  //   string recordKey = "non_existing_key";

  //   // Act: Try to get a record from a non-existing collection
  //   var fetchedRecord = await this._astraDbMemoryStore.GetAsync(collection, recordKey);

  //   // Assert: Ensure the method returns null
  //   Assert.Null(fetchedRecord);
  // }

  #region private ================================================================================

  private string _apiEndpoint = "https://442a1e50-7aa9-4fd1-89e2-b3ae5e0416b4-us-east-2.apps.astra.datastax.com"!;
  private string _appToken = "AstraCS:bdbaZqEvgmxUTMzjHZGHFEfJ:a02576b09df841c928dcebc27f2e990d8f168bb3f67c1290480a2207a4d85eb8";
  private string _keySpace = "default_keyspace";

  private AstraDBMemoryStore CreateMemoryStore()
  {
    return new AstraDBMemoryStore(this._apiEndpoint!, this._appToken, this._keySpace, 5);
  }

  private readonly AstraDBMemoryStore _astraDbMemoryStore;
  #endregion
}