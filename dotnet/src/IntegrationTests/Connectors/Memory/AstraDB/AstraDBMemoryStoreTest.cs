using System;
using System.Linq;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AstraDB;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.AstraDB;
public class AstraDBMemoryStoreTests : IAsyncLifetime
{
  // all tests are enabled if it sets null
  private const string? SkipReason = "Astra Database is required for tests";

  private readonly ITestOutputHelper _output;

  public AstraDBMemoryStoreTests(ITestOutputHelper output)
  {
    _output = output;
  }
  public async Task InitializeAsync()
  {
    // Load configuration
    var configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AstraDBMemoryStoreTests>()
        .Build();

    this._keySpace = configuration["AstraDB:KeySpace"] ?? "default_keyspace";
    this._apiEndpoint = configuration["AstraDB:ApiEndpoint"] ?? "";
    this._appToken = configuration["AstraDB:AppToken"] ?? "";
    this._vectorSize = int.Parse(configuration["AstraDB:VectorSize"] ?? "5"); // it should be given 5 for tests
  }
  public async Task DisposeAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    await foreach (var dbcollectionName in astraDbMemoryStore.GetCollectionsAsync())
    {
      await astraDbMemoryStore.DeleteCollectionAsync(dbcollectionName);
    }
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanCreateAndGetCollectionAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection
    string collection = "vector_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var collectionNames = astraDbMemoryStore.GetCollectionsAsync();

    Assert.True(await collectionNames.ContainsAsync(collection));
  }
  [Fact(Skip = SkipReason)]
  public async Task ItCanCheckIfCollectionExistsAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection
    string collection = "vector_search_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    Assert.True(await astraDbMemoryStore.DoesCollectionExistAsync("vector_search_collection"));
    Assert.False(await astraDbMemoryStore.DoesCollectionExistAsync("non_vector_search_collection"));
  }
  [Fact(Skip = SkipReason)]
  public async Task ItCanDeleteCollectionAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection
    string collection = "collection_to_delete";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    // Ensure the collection exists before deletion
    Assert.True(await astraDbMemoryStore.DoesCollectionExistAsync(collection));

    // Act: Delete the collection
    await astraDbMemoryStore.DeleteCollectionAsync(collection);

    // Assert: Ensure the collection no longer exists
    Assert.False(await astraDbMemoryStore.DoesCollectionExistAsync(collection));
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanUpsertRecordAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection
    string collection = "test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecord = MemoryRecord.LocalRecord(
            id: "test_id",
            text: "test_text",
            description: "test_description",
            embedding: new float[] { 1, 2, 3, 4, 5 });

    var upsertedKey = await astraDbMemoryStore.UpsertAsync(collection, testRecord);

    Assert.Equal(testRecord.Metadata.Id, upsertedKey);
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanUpsertBatchRecordsAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection
    string collection = "test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

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

    await foreach (var key in astraDbMemoryStore.UpsertBatchAsync(collection, testRecords))
    {
      upsertedKeys.Add(key);
    }

    Assert.Equal(testRecords.Count, upsertedKeys.Count);

    foreach (var record in testRecords)
    {
      Assert.Contains(record.Metadata.Id, upsertedKeys);
    }
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanGetRecordAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection and insert a record
    string collection = "get_test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecord = MemoryRecord.LocalRecord(
        id: "test_id",
        text: "test_text",
        description: "test_description",
        embedding: new float[] { 1, 2, 3, 4, 5 });

    await astraDbMemoryStore.UpsertAsync(collection, testRecord);

    // Act: Get the record
    var fetchedRecord = await astraDbMemoryStore.GetAsync(collection, testRecord.Key);
    // Assert: Ensure the record was fetched correctly
    Assert.NotNull(fetchedRecord);
    Assert.Equal(testRecord.Key, fetchedRecord.Key);
    Assert.Equal(testRecord.Metadata.Id, fetchedRecord.Metadata.Id);
    Assert.Equal(testRecord.Metadata.Text, fetchedRecord.Metadata.Text);
    Assert.Equal(testRecord.Metadata.Description, fetchedRecord.Metadata.Description);
    Assert.Equal(testRecord.Embedding.ToArray(), fetchedRecord.Embedding.ToArray());
  }

  [Fact(Skip = SkipReason)]
  public async Task GetAsyncReturnsNullIfCollectionDoesNotExist()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Use a non-existing collection name
    string collection = "non_existing_collection";
    string recordKey = "non_existing_key";

    // Act: Try to get a record from a non-existing collection
    var fetchedRecord = await astraDbMemoryStore.GetAsync(collection, recordKey);

    // Assert: Ensure the method returns null
    Assert.Null(fetchedRecord);
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanGetBatchRecordsAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection and insert multiple records
    string collection = "batch_test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

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
    await foreach (var key in astraDbMemoryStore.UpsertBatchAsync(collection, testRecords))
    {
      upsertedKeys.Add(key);
    }

    // Act: Retrieve the batch records
    var keys = upsertedKeys;
    var fetchedRecords = new List<MemoryRecord>();
    await foreach (var record in astraDbMemoryStore.GetBatchAsync(collection, keys))
    {
      fetchedRecords.Add(record);
    }

    // Assert: Ensure all records were fetched correctly
    Assert.Equal(testRecords.Count, fetchedRecords.Count);
    foreach (var testRecord in testRecords)
    {
      var fetchedRecord = fetchedRecords.First(r => r.Key == testRecord.Key);
      Assert.Equal(testRecord.Metadata.Id, fetchedRecord.Metadata.Id);
      Assert.Equal(testRecord.Metadata.Text, fetchedRecord.Metadata.Text);
      Assert.Equal(testRecord.Metadata.Description, fetchedRecord.Metadata.Description);
      Assert.Equal(testRecord.Embedding.ToArray(), fetchedRecord.Embedding.ToArray());
    }
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanDeleteRecordAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection and insert a record
    string collection = "delete_test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecord = MemoryRecord.LocalRecord(
        id: "test_id",
        text: "test_delete_text",
        description: "test_description",
        embedding: new float[] { 1, 2, 3, 4, 5 });

    await astraDbMemoryStore.UpsertAsync(collection, testRecord);

    await astraDbMemoryStore.RemoveAsync(collection, testRecord.Key);

    var fetchedRecord = await astraDbMemoryStore.GetAsync(collection, testRecord.Key);
    Assert.Null(fetchedRecord);
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanDeleteManyRecordsAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection and insert multiple records
    string collection = "delete_many_test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecords = Enumerable.Range(1, 5).Select(i => MemoryRecord.LocalRecord(
        id: $"batch_test_id_{i}",
        text: $"batch_test_text_{i}",
        description: $"batch_test_description_{i}",
        embedding: new float[] { 1, 2, 3, 4, 5 }
    )).ToList();

    await foreach (var key in astraDbMemoryStore.UpsertBatchAsync(collection, testRecords)) { }

    // Act: Delete the records
    var keys = testRecords.Select(r => r.Key).ToList();
    await astraDbMemoryStore.RemoveBatchAsync(collection, keys, CancellationToken.None);

    // Assert: Ensure the records were deleted
    foreach (var key in keys)
    {
      var fetchedRecord = await astraDbMemoryStore.GetAsync(collection, key);
      Assert.Null(fetchedRecord);
    }
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanGetNearestMatchesAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();

    // Arrange: Create a collection and insert multiple records
    string collection = "nearest_matches_test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecords = new List<MemoryRecord>
            {
                MemoryRecord.LocalRecord(
                    id: "nearest_test_id_1",
                    text: "nearest_test_text_1",
                    description: "nearest_test_description_1",
                    embedding: new float[] { 0.1f, 0.2f, 0.3f, 0.4f, 0.5f }),
                MemoryRecord.LocalRecord(
                    id: "nearest_test_id_2",
                    text: "nearest_test_text_2",
                    description: "nearest_test_description_2",
                    embedding: new float[] { 0.2f, 0.3f, 0.4f, 0.5f, 0.6f }),
                MemoryRecord.LocalRecord(
                    id: "nearest_test_id_3",
                    text: "nearest_test_text_3",
                    description: "nearest_test_description_3",
                    embedding: new float[] { 0.3f, 0.4f, 0.5f, 0.6f, 0.7f })
            };

    var upsertedKeys = new List<string>();
    await foreach (var key in astraDbMemoryStore.UpsertBatchAsync(collection, testRecords))
    {
      upsertedKeys.Add(key);
    }

    // Act: Retrieve the nearest matches
    var queryEmbedding = new ReadOnlyMemory<float>(new float[] { 0.25f, 0.35f, 0.45f, 0.55f, 0.65f });
    var nearestMatches = new List<(MemoryRecord, double)>();
    await foreach (var match in astraDbMemoryStore.GetNearestMatchesAsync(collection, queryEmbedding, 3, 0.8, true))
    {
      nearestMatches.Add(match);
    }

    // Assert: Ensure the nearest matches were fetched correctly
    Assert.Equal(3, nearestMatches.Count);
    foreach (var match in nearestMatches)
    {
      Assert.Contains(testRecords, record => record.Key == match.Item1.Key);
    }
  }

  [Fact(Skip = SkipReason)]
  public async Task ItCanGetNearestMatchAsync()
  {
    AstraDBMemoryStore astraDbMemoryStore = this.CreateMemoryStore();
    // Arrange: Create a collection and insert multiple records
    string collection = "nearest_match_test_collection";
    await astraDbMemoryStore.CreateCollectionAsync(collection);

    var testRecords = new List<MemoryRecord>
    {
        MemoryRecord.LocalRecord(
            id: "nearest_test_id_1",
            text: "nearest_test_text_1",
            description: "nearest_test_description_1",
            embedding: new float[] { 0.1f, 0.2f, 0.3f, 0.4f, 0.5f }),
        MemoryRecord.LocalRecord(
            id: "nearest_test_id_2",
            text: "nearest_test_text_2",
            description: "nearest_test_description_2",
            embedding: new float[] { 0.2f, 0.3f, 0.4f, 0.5f, 0.6f }),
        MemoryRecord.LocalRecord(
            id: "nearest_test_id_3",
            text: "nearest_test_text_3",
            description: "nearest_test_description_3",
            embedding: new float[] { 0.3f, 0.4f, 0.5f, 0.6f, 0.7f })
    };

    var upsertedKeys = new List<string>();
    await foreach (var key in astraDbMemoryStore.UpsertBatchAsync(collection, testRecords))
    {
      upsertedKeys.Add(key);
    }

    // Act: Retrieve the nearest match
    var queryEmbedding = new ReadOnlyMemory<float>(new float[] { 0.25f, 0.35f, 0.45f, 0.55f, 0.65f });
    var nearestMatch = await astraDbMemoryStore.GetNearestMatchAsync(collection, queryEmbedding, 0.8, true);

    // Assert: Ensure the nearest match was fetched correctly
    Assert.NotNull(nearestMatch);
    var (record, similarity) = nearestMatch.Value;
    Assert.Contains(testRecords, r => r.Key == record.Key);
    Assert.True(similarity >= 0.8);
  }

  #region private ================================================================================

  private string _apiEndpoint = "";
  private string _appToken = "";
  private string _keySpace = "";
  private int _vectorSize;

  private AstraDBMemoryStore CreateMemoryStore()
  {
    return new AstraDBMemoryStore(this._apiEndpoint!, this._appToken, this._keySpace, this._vectorSize);
  }
  #endregion
}