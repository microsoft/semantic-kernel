// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using Grpc.Net.Client;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;
using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class PineconeTestStore : TestStore
{
    // Values taken from https://docs.pinecone.io/guides/operations/local-development
    private const string Image = "ghcr.io/pinecone-io/pinecone-local:v0.7.0";
    private const ushort RestPort = 5080;
    private const ushort GrpcPort = RestPort + 1;

    public static PineconeTestStore Instance { get; } = new();

    private IContainer? _container;
    private Pinecone.PineconeClient? _client;
    private PineconeVectorStore? _defaultVectorStore;

    public Pinecone.PineconeClient Client => this._client ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private PineconeTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        this._container = await this.CreateContainerAsync();

        string restUrl = $"http://{this._container.Hostname}:{this._container.GetMappedPublicPort(RestPort)}";
        string grpcUrl = $"http://{this._container.Hostname}:{this._container.GetMappedPublicPort(GrpcPort)}";

        GrpcChannelOptions grpcOptions = new()
        {
            HttpClient = new()
            {
                BaseAddress = new(grpcUrl)
            }
        };

        ClientOptions clientOptions = new()
        {
            BaseUrl = restUrl,
            MaxRetries = 0,
            IsTlsEnabled = false,
            GrpcOptions = grpcOptions
        };

        this._client = new Pinecone.PineconeClient(
            apiKey: "ForPineconeLocalTheApiKeysAreIgnored",
            clientOptions: clientOptions);

        this._defaultVectorStore = new(this._client);
    }

    protected override async Task StopAsync()
    {
        if (this._container is not null)
        {
            await this._container.DisposeAsync();
        }
    }

    private async Task<IContainer> CreateContainerAsync()
    {
        var container = new ContainerBuilder()
            .WithImage(Image)
            .WithPortBinding(RestPort, assignRandomHostPort: true)
            .WithPortBinding(GrpcPort, assignRandomHostPort: true)
            .Build();

        await container.StartAsync();

        return container;
    }
}
