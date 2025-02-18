using System.Linq;
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

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanInsertAndDeleteRecord(bool deleteBatch)
    {
        SqlServerTestStore testStore = new();

        await testStore.ReferenceCountingStartAsync();

        var collection = testStore.DefaultVectorStore.GetCollection<string, TestModel>("other");

        try
        {
            await collection.CreateCollectionIfNotExistsAsync();

            ReadOnlyMemory<float> floats = Enumerable.Range(0, 10).Select(i => (float)i).ToArray();
            string key = await collection.UpsertAsync(new TestModel()
            {
                Id = "MyId",
                Number = 100,
                Floats = floats
            });
            Assert.Equal("MyId", key);

            TestModel? record = await collection.GetAsync("MyId");
            Assert.NotNull(record);
            Assert.Equal(100, record.Number);
            Assert.Equal("MyId", record.Id);
            Assert.Equal(floats, record.Floats);
            Assert.Null(record.Text);

            record = await collection.GetBatchAsync(["MyId"]).SingleAsync();
            Assert.NotNull(record);
            Assert.Equal(100, record.Number);
            Assert.Equal("MyId", record.Id);
            Assert.Equal(floats, record.Floats);
            Assert.Null(record.Text);

            if (deleteBatch)
            {
                await collection.DeleteBatchAsync(["MyId"]);
            }
            else
            {
                await collection.DeleteAsync("MyId");
            }

            Assert.Null(await collection.GetAsync("MyId"));
            Assert.False(await collection.GetBatchAsync(["MyId"]).AnyAsync());
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

        [VectorStoreRecordData(StoragePropertyName = "text")]
        public string? Text { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "column")]
        public int Number { get; set; }

        [VectorStoreRecordVector(Dimensions: 10, StoragePropertyName = "embedding")]
        public ReadOnlyMemory<float> Floats { get; set; }
    }
}
