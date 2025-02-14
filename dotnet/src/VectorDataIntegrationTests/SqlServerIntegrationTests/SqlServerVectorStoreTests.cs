using Microsoft.Extensions.VectorData;
using SqlServerIntegrationTests.Support;
using Xunit;

namespace SqlServerIntegrationTests;

public class SqlServerVectorStoreTests
{
    [Fact]
    public async Task CanCreateAndDeleteTheCollections()
    {
        SqlServerTestStore testStore = new();

        await testStore.ReferenceCountingStartAsync();

        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>("collection");

        try
        {
            Assert.False(await collection.CollectionExistsAsync());

            await collection.CreateCollectionAsync();

            Assert.True(await collection.CollectionExistsAsync());

            await collection.CreateCollectionIfNotExistsAsync();

            Assert.True(await collection.CollectionExistsAsync());

            await collection.DeleteCollectionAsync();

            Assert.False(await collection.CollectionExistsAsync());
        }
        finally
        {
            await collection.DeleteCollectionAsync();

            await testStore.ReferenceCountingStopAsync();
        }
    }

    public sealed class TestModel
    {
        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public string Id { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "column")]
        public int Number { get; set; }
    }
}
