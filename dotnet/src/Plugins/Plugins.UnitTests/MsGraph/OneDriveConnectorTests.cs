// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.Kiota.Abstractions.Authentication;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.MsGraph;

public sealed class OneDriveConnectorTests
{
    [Fact]
    public async Task UploadUsesProvidedStreamAndLeavesItOpenAsync()
    {
        using var handler = new UploadHandler();
        using var client = new HttpClient(handler);
        using var graph = new GraphServiceClient(client, new AnonymousAuthenticationProvider());
        var connector = new OneDriveConnector(graph);
        using var content = new MemoryStream(Encoding.UTF8.GetBytes("prefix-content"));
        content.Position = 7;

        await connector.UploadSmallFileAsync(content, "/file.txt");

        Assert.Equal("content", Encoding.UTF8.GetString(handler.UploadedContent!));
        Assert.True(content.CanRead);
    }

    [Fact]
    public async Task OversizeStreamIsRejectedBeforeSendingRequestAsync()
    {
        using var handler = new UploadHandler();
        using var client = new HttpClient(handler);
        using var graph = new GraphServiceClient(client, new AnonymousAuthenticationProvider());
        var connector = new OneDriveConnector(graph);
        using var content = new MemoryStream(new byte[(4 * 1024 * 1024) + 1]);

        await Assert.ThrowsAsync<IOException>(() => connector.UploadSmallFileAsync(content, "/file.txt"));
        Assert.Equal(0, handler.RequestCount);
        Assert.True(content.CanRead);
    }

    private sealed class UploadHandler : HttpMessageHandler
    {
        internal byte[]? UploadedContent { get; private set; }

        internal int RequestCount { get; private set; }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.RequestCount++;
            if (request.Method == HttpMethod.Put)
            {
                this.UploadedContent = await request.Content!.ReadAsByteArrayAsync(cancellationToken);
            }

            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("{\"id\":\"test-drive\"}", Encoding.UTF8, "application/json")
            };
        }
    }
}
