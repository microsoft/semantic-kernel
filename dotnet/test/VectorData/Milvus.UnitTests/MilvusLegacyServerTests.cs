// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Milvus;
using Microsoft.SemanticKernel.Memory;
using Testcontainers.Milvus;
using Xunit;

namespace SemanticKernel.Connectors.Milvus.UnitTests;

public sealed class MilvusLegacyFixture : MilvusFixture
{
    public MilvusLegacyFixture() : base("milvusdb/milvus:v2.2.14")
    {
    }
}

[Trait("Category", "MilvusIntegration")]
public sealed class MilvusLegacyServerTests : IAsyncLifetime
{
    private readonly MilvusLegacyFixture _fixture = new();

    public Task InitializeAsync() => this._fixture.InitializeAsync();

    public Task DisposeAsync() => this._fixture.DisposeAsync();

    // For manual testing with Docker only. Remove Skip locally to enable this test.
    [Fact(Skip = "For manual testing only; requires Docker.")]
    public async Task RejectsOldServerBeforeReadingOrChangingRecordsAsync()
    {
        using MilvusMemoryStore store = new(
            this._fixture.Container.Hostname,
            port: this._fixture.Container.GetMappedPublicPort(MilvusBuilder.MilvusGrpcPort));
        const string CollectionName = "does_not_exist";
        const string Key = "a\",\"victim";
        MemoryRecord record = MemoryRecord.LocalRecord(Key, "synthetic", null, new float[] { 1, 0 });

        await Assert.ThrowsAsync<NotSupportedException>(() => store.GetAsync(CollectionName, Key));
        await Assert.ThrowsAsync<NotSupportedException>(() => store.GetBatchAsync(CollectionName, [Key]).ToListAsync().AsTask());
        await Assert.ThrowsAsync<NotSupportedException>(() => store.RemoveAsync(CollectionName, Key));
        await Assert.ThrowsAsync<NotSupportedException>(() => store.RemoveBatchAsync(CollectionName, [Key]));
        await Assert.ThrowsAsync<NotSupportedException>(() => store.UpsertAsync(CollectionName, record));
        await Assert.ThrowsAsync<NotSupportedException>(() => store.UpsertBatchAsync(CollectionName, [record]).ToListAsync().AsTask());
        await Assert.ThrowsAsync<NotSupportedException>(() => store.GetNearestMatchAsync(CollectionName, new float[] { 1, 0 }, withEmbedding: true));
        await Assert.ThrowsAsync<NotSupportedException>(() => store.GetNearestMatchesAsync(
            CollectionName, new float[] { 1, 0 }, limit: 1, withEmbeddings: true).ToListAsync().AsTask());
    }
}
