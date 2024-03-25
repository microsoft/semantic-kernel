// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Milvus.Client;
using Testcontainers.Milvus;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Milvus;

public sealed class MilvusFixture : IAsyncLifetime
{
    private readonly MilvusContainer _container = new MilvusBuilder().Build();

    public string Host => this._container.Hostname;
    public int Port => this._container.GetMappedPublicPort(MilvusBuilder.MilvusGrpcPort);

    public MilvusClient CreateClient()
        => new(this.Host, "root", "milvus", this.Port);

    public Task InitializeAsync()
        => this._container.StartAsync();

    public Task DisposeAsync()
        => this._container.DisposeAsync().AsTask();
}
