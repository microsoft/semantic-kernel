// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System.Net.Http;
#pragma warning restore IDE0005 // Using directive is unnecessary.
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Containers;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Pinecone;
using VectorDataSpecificationTests.Support;

namespace PineconeIntegrationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable
#pragma warning disable CA2000 // Dispose objects before losing scope

internal sealed class PineconeTestStore : TestStore
{
    // Values taken from https://docs.pinecone.io/guides/operations/local-development
    // v0.7.0 works with 2.1 client
    // v1.0.0 works with 3.0 client
    // We use hardcoded version to avoid breaking changes.
    private const string Image = "ghcr.io/pinecone-io/pinecone-local:v1.0.0.rc0";
    private const ushort FirstPort = 5080;
    private const int IndexServiceCount = 10;

    public static PineconeTestStore Instance { get; } = new();

    private IContainer? _container;
    private Pinecone.PineconeClient? _client;
    private PineconeVectorStore? _defaultVectorStore;

    public Pinecone.PineconeClient Client => this._client ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public PineconeVectorStore GetVectorStore(PineconeVectorStoreOptions options)
        => new(this.Client, options);

    // Pinecone does not support distance functions other than PGA which is always enabled.
    public override string DefaultIndexKind => "";

    private PineconeTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        this._container = await this.StartContainerAsync();

        Dictionary<int, int> containerToHostPort = Enumerable.Range(FirstPort, IndexServiceCount + 1)
            .ToDictionary(port => port, port => (int)this._container.GetMappedPublicPort(port));

        UriBuilder baseAddress = new()
        {
            Scheme = "http",
            Host = this._container.Hostname,
            Port = this._container.GetMappedPublicPort(FirstPort)
        };

        ClientOptions clientOptions = new()
        {
            BaseUrl = baseAddress.Uri.ToString(),
            MaxRetries = 0,
            IsTlsEnabled = false,
            GrpcOptions = new()
            {
                HttpClient = new(new RedirectHandler(containerToHostPort), disposeHandler: true)
                {
                    BaseAddress = baseAddress.Uri
                },
            }
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

    private async Task<IContainer> StartContainerAsync()
    {
        ContainerBuilder builder = new ContainerBuilder()
            .WithImage(Image)
            // Pinecone Local will run on port $FirstPort.
            .WithPortBinding(FirstPort, assignRandomHostPort: true)
            // We are currently using the default Pinecone port (5080), but we can change it to a random port.
            // In such case, we are going to need to set the PORT environment variable to the new port.
            .WithEnvironment("PORT", FirstPort.ToString());

        for (int indexService = 1; indexService <= IndexServiceCount; indexService++)
        {
            // And the index services on the following ports.
            builder = builder.WithPortBinding(FirstPort + indexService, assignRandomHostPort: true);
        }

        var container = builder.Build();

        await container.StartAsync();

        return container;
    }

    private sealed class RedirectHandler : DelegatingHandler
    {
        private readonly Dictionary<int, int> _containerToHostPort;

        public RedirectHandler(Dictionary<int, int> portRedirections)
            : base(new HttpClientHandler())
        {
            this._containerToHostPort = portRedirections;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // When "host" argument is not provided for PineconeClient.Index,
            // it will try to get the host from the Pinecone service.
            // In the cloud environment it's fine, but with the local emulator
            // it reports the address with the container port, not the host port.
            if (request.RequestUri != null && request.RequestUri.IsAbsoluteUri
                && request.RequestUri.Host == "localhost"
                && this._containerToHostPort.TryGetValue(request.RequestUri.Port, out int hostPort))
            {
                UriBuilder builder = new(request.RequestUri)
                {
                    Port = hostPort
                };
                request.RequestUri = builder.Uri;
            }

            return base.SendAsync(request, cancellationToken);
        }
    }
}
