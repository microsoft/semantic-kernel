// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqliteVec;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.SqliteVec;

/// <summary>
/// Integration tests for <see cref="SqliteVectorStore"/> class.
/// </summary>
[Collection("SqliteVectorStoreCollection")]
public sealed class SqliteVectorStoreTests(SqliteVectorStoreFixture fixture)
#pragma warning disable CA2000 // Dispose objects before losing scope
    : BaseVectorStoreTests<string, SqliteHotel<string>>(new SqliteVectorStore(fixture.ConnectionString))
#pragma warning restore CA2000 // Dispose objects before losing scope
{
    [VectorStoreFact]
    public async Task ItCanGetAListOfExistingCollectionNamesWhenRegisteredWithDIAsync()
    {
        // Arrange
        var serviceCollection = new ServiceCollection();

        serviceCollection.AddSqliteVectorStore(_ => fixture.ConnectionString);

        var provider = serviceCollection.BuildServiceProvider();

        var sut = provider.GetRequiredService<VectorStore>();

        var collection1 = sut.GetCollection<string, SqliteHotel<string>>("ListCollectionNames1");
        var collection2 = sut.GetCollection<string, SqliteHotel<string>>("ListCollectionNames2");

        await collection1.EnsureCollectionExistsAsync();
        await collection2.EnsureCollectionExistsAsync();

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("ListCollectionNames1", collectionNames);
        Assert.Contains("ListCollectionNames1", collectionNames);
    }
}
