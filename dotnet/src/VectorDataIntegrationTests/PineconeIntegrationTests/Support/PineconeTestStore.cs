// Copyright (c) Microsoft. All rights reserved.

using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using Microsoft.Extensions.VectorData;
using Pinecone;
using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class PineconeTestStore : TestStore
{
    // Values taken from https://docs.pinecone.io/guides/operations/local-development
    private const string Image = "ghcr.io/pinecone-io/pinecone-local:v0.7.0";
    private const ushort HttpPort = 5080;
    private const string Host = "localhost";

    public static PineconeTestStore Instance { get; } = new();

    private IContainer? _container;
    private PineconeClient? _client;
    private IVectorStore? _defaultVectorStore;

    public PineconeClient Client => this._client ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private PineconeTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        this._container = await this.CreateContainerAsync();

        string url = $"http://{this._container.Hostname}:{this._container.GetMappedPublicPort(HttpPort)}";

        this._client = new PineconeClient(
            apiKey: "ForPineconeLocalTheApiKeysAreIgnored",
            clientOptions: new()
            {
                BaseUrl = url,
                MaxRetries = 0,
                IsTlsEnabled = false
            });
        //this._defaultVectorStore = new(this._client);

        Console.WriteLine(url);
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
            .WithPortBinding(HttpPort, assignRandomHostPort: true)
            .WithEnvironment("PINECONE_HOST", "localhost")
            .WithEnvironment("PORT", HttpPort.ToString())
            .WithHostname(Host)
            .WithExposedPort(HttpPort)
            //.WithWaitStrategy(Wait.ForUnixContainer().UntilHttpRequestIsSucceeded(r => r.ForPort(HttpPort)))
            //.WithWaitStrategy(Wait.ForUnixContainer().UntilPortIsAvailable(HttpPort))
            //.WithWaitStrategy(Wait.ForUnixContainer().UntilMessageIsLogged(".*Emulating a Pinecone serverless index.*"))
            .Build();

        await container.StartAsync();

        return container;
    }
}
