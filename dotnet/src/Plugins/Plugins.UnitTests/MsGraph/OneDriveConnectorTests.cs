// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;
using Microsoft.Kiota.Abstractions.Authentication;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.MsGraph;

public sealed class OneDriveConnectorTests
{
    [Theory]
    [InlineData("read", "/Uploads/Sub/../report.txt", "/Uploads/report.txt", ":/content")]
    [InlineData("share", "/Uploads/Sub/../report.txt", "/Uploads/report.txt", ":/createLink")]
    [InlineData("upload", "/Uploads/Sub/../report.txt", "/Uploads/report.txt", ":/content")]
    [InlineData("read", "/Uploads/a%20b.txt", "/Uploads/a%20b.txt", ":/content")]
    [InlineData("share", "/Uploads/a%20b.txt", "/Uploads/a%20b.txt", ":/createLink")]
    [InlineData("upload", "/Uploads/a%20b.txt", "/Uploads/a%20b.txt", ":/content")]
    public async Task PluginAuthorizationAndGraphRequestUseTheSameRemotePathAsync(
        string operation,
        string suppliedPath,
        string expectedPath,
        string requestSuffix)
    {
        using var handler = new GraphRequestHandler();
        using var client = new HttpClient(handler);
        using var graph = new GraphServiceClient(client, new AnonymousAuthenticationProvider());
        var connector = new OneDriveConnector(graph);
        var tempDirectory = Path.Combine(Path.GetTempPath(), $"OneDriveConnectorTests_{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDirectory);
        var sourcePath = Path.Combine(tempDirectory, "source.txt");
        await File.WriteAllTextAsync(sourcePath, "content");
        try
        {
            var plugin = new CloudDrivePlugin(connector)
            {
                AllowedReadPaths = ["/Uploads"],
                AllowedSharePaths = ["/Uploads"],
                AllowedUploadDirectories = [tempDirectory],
                AllowedUploadDestinationPaths = ["/Uploads"]
            };

            switch (operation)
            {
                case "read":
                    Assert.Equal("content", await plugin.GetFileContentAsync(suppliedPath));
                    break;
                case "share":
                    Assert.Equal("https://example.com/share", await plugin.CreateLinkAsync(suppliedPath));
                    break;
                case "upload":
                    await plugin.UploadFileAsync(sourcePath, suppliedPath);
                    break;
                default:
                    throw new InvalidOperationException($"Unknown test operation '{operation}'.");
            }

            Assert.NotNull(handler.OperationRequestUri);
            Assert.Equal(
                $"/v1.0/drives/test-drive/root:{expectedPath}{requestSuffix}",
                handler.OperationRequestUri.AbsolutePath);
        }
        finally
        {
            Directory.Delete(tempDirectory, recursive: true);
        }
    }

    [Theory]
    [InlineData("read")]
    [InlineData("share")]
    [InlineData("upload")]
    public async Task EncodedTraversalIsRejectedBeforeAnyGraphRequestAsync(string operation)
    {
        using var handler = new GraphRequestHandler();
        using var client = new HttpClient(handler);
        using var graph = new GraphServiceClient(client, new AnonymousAuthenticationProvider());
        var plugin = new CloudDrivePlugin(new OneDriveConnector(graph))
        {
            AllowedReadPaths = ["/Uploads"],
            AllowedSharePaths = ["/Uploads"],
            AllowedUploadDestinationPaths = ["/Uploads"]
        };
        const string Path = "/Uploads/%2e%2e/Confidential/secret.txt";

        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
        {
            switch (operation)
            {
                case "read":
                    await plugin.GetFileContentAsync(Path);
                    break;
                case "share":
                    await plugin.CreateLinkAsync(Path);
                    break;
                case "upload":
                    await plugin.UploadFileAsync("unused.txt", Path);
                    break;
            }
        });

        Assert.Equal(0, handler.RequestCount);
    }

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

    private sealed class GraphRequestHandler : HttpMessageHandler
    {
        internal int RequestCount { get; private set; }

        internal Uri? OperationRequestUri { get; private set; }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.RequestCount++;
            var path = request.RequestUri!.AbsolutePath;
            if (path.EndsWith("/me/drive", StringComparison.Ordinal))
            {
                return JsonResponse("{\"id\":\"test-drive\"}");
            }

            this.OperationRequestUri = request.RequestUri;
            if (request.Method == HttpMethod.Put)
            {
                _ = await request.Content!.ReadAsByteArrayAsync(cancellationToken);
                return JsonResponse("{\"id\":\"uploaded\"}");
            }

            if (request.Method == HttpMethod.Post)
            {
                return JsonResponse("{\"link\":{\"webUrl\":\"https://example.com/share\"}}");
            }

            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("content", Encoding.UTF8, "text/plain")
            };
        }

        private static HttpResponseMessage JsonResponse(string json) =>
            new(HttpStatusCode.OK)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json")
            };
    }
}
