// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using DotNet.Testcontainers.Networks;
using Testcontainers.Milvus;
using Xunit;

namespace SemanticKernel.Connectors.Milvus.UnitTests;

public class MilvusFixture : IAsyncLifetime
{
    private readonly INetwork _network = new NetworkBuilder().Build();
    private readonly IContainer _storage;

    public MilvusFixture() : this("milvusdb/milvus:v2.3.0")
    {
    }

    protected MilvusFixture(string image)
    {
        string password = Guid.NewGuid().ToString("N");
        this._storage = new ContainerBuilder("milvusdb/minio:RELEASE.2024-12-18T13-15-44Z")
            .WithNetwork(this._network)
            .WithNetworkAliases("minio")
            .WithEnvironment("MINIO_ROOT_USER", "test-user")
            .WithEnvironment("MINIO_ROOT_PASSWORD", password)
            .WithCommand("server", "/data")
            .WithPortBinding(9000, true)
            .WithWaitStrategy(Wait.ForUnixContainer().UntilHttpRequestIsSucceeded(
                request => request.ForPort(9000).ForPath("/minio/health/live")))
            .Build();

        // Milvus 2.2 needs object storage; the module's local-storage default requires a newer server.
        this.Container = new MilvusBuilder(image)
            .WithNetwork(this._network)
            .WithEnvironment("COMMON_STORAGETYPE", "minio")
            .WithEnvironment("MINIO_ADDRESS", "minio:9000")
            .WithEnvironment("MINIO_ACCESS_KEY_ID", "test-user")
            .WithEnvironment("MINIO_SECRET_ACCESS_KEY", password)
            .WithWaitStrategy(Wait.ForUnixContainer().UntilHttpRequestIsSucceeded(
                request => request.ForPort(MilvusBuilder.MilvusManagementPort).ForPath("/healthz"),
                strategy => strategy.WithTimeout(TimeSpan.FromMinutes(2))))
            .Build();
    }

    public MilvusContainer Container { get; }

    public async Task InitializeAsync()
    {
        await this._network.CreateAsync();
        await this._storage.StartAsync();
        await this.Container.StartAsync();
    }

    public async Task DisposeAsync()
    {
        try
        {
            await this.Container.DisposeAsync();
        }
        finally
        {
            try
            {
                await this._storage.DisposeAsync();
            }
            finally
            {
                await this._network.DisposeAsync();
            }
        }
    }
}
