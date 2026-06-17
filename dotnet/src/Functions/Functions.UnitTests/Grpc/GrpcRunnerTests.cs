// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Grpc;
using Microsoft.SemanticKernel.Plugins.Grpc.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Grpc;

public sealed class GrpcRunnerTests : IDisposable
{
    /// <summary>
    /// An instance of HttpMessageHandlerStub class used to get access to various properties of HttpRequestMessage sent by HTTP client.
    /// </summary>
    private readonly HttpMessageHandlerStub _httpMessageHandlerStub;

    /// <summary>
    /// An instance of HttpClient class used by the tests.
    /// </summary>
    private readonly HttpClient _httpClient;

    /// <summary>
    /// Creates an instance of a <see cref="GrpcRunnerTests"/> class.
    /// </summary>
    public GrpcRunnerTests()
    {
        this._httpMessageHandlerStub = new HttpMessageHandlerStub();

        this._httpClient = new HttpClient(this._httpMessageHandlerStub);
    }

    [Fact]
    public async Task ShouldUseAddressProvidedInGrpcOperationAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);

        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://fake-random-test-host"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/greet.Greeter/SayHello", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldIgnoreAddressFromArgumentsAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);

        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://fake-random-test-host"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) },
            { "address", "https://evil-host-from-llm" }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert - LLM-supplied address should be ignored, operation address should be used
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/greet.Greeter/SayHello", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldUseAddressOverrideFromParametersAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var addressOverride = new Uri("https://developer-override-host");
        var sut = new GrpcOperationRunner(this._httpClient, addressOverride: addressOverride);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://fake-random-test-host"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert - developer-provided override takes precedence
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.StartsWith("https://developer-override-host/", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldRejectAddressNotInAllowlistAsync()
    {
        // Arrange
        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var allowedAddresses = new[] { new Uri("https://allowed-host.com/") };
        var sut = new GrpcOperationRunner(this._httpClient, allowedAddresses: allowedAddresses);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://not-allowed-host.com"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act & Assert
        var ex = await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
        Assert.Contains("not allowed", ex.Message);
    }

    [Fact]
    public async Task ShouldAllowAddressInAllowlistAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var allowedAddresses = new[] { new Uri("https://fake-random-test-host/") };
        var sut = new GrpcOperationRunner(this._httpClient, allowedAddresses: allowedAddresses);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://fake-random-test-host"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert - should succeed
        Assert.NotNull(result);
    }

    [Fact]
    public async Task ShouldAllowAddressWithSubPathWhenAllowlistHasTrailingSlashAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var allowedAddresses = new[] { new Uri("https://fake-random-test-host/grpc/") };
        var sut = new GrpcOperationRunner(this._httpClient, allowedAddresses: allowedAddresses);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://fake-random-test-host/grpc/v1"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert - trailing slash in allowlist should allow sub-paths
        Assert.NotNull(result);
    }

    [Fact]
    public async Task ShouldAllowHttpWhenCustomSchemesPermitItAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var allowedSchemes = new[] { "https", "http" };
        var sut = new GrpcOperationRunner(this._httpClient, allowedSchemes: allowedSchemes);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "http://localhost"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert - http should be allowed when custom schemes permit it
        Assert.NotNull(result);
    }

    [Fact]
    public async Task ShouldRejectNonHttpsSchemeByDefaultAsync()
    {
        // Arrange
        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "http://insecure-host.com"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act & Assert
        var ex = await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
        Assert.Contains("scheme", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ShouldRejectAddressThatSharesPrefixButIsNotAtPathBoundaryAsync()
    {
        // Arrange - allowlist without trailing slash, address extends the path segment
        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var allowedAddresses = new[] { new Uri("https://api.example.com/grpc") };
        var sut = new GrpcOperationRunner(this._httpClient, allowedAddresses: allowedAddresses);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://api.example.com/grpcevil"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act & Assert - "grpcevil" should NOT match "grpc" since it's not at a path boundary
        var ex = await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
        Assert.Contains("not allowed", ex.Message);
    }

    [Fact]
    public async Task ShouldRejectAddressOverrideNotInAllowlistAsync()
    {
        // Arrange
        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var allowedAddresses = new[] { new Uri("https://allowed-host.com/") };
        var addressOverride = new Uri("https://evil-host.com/");
        var sut = new GrpcOperationRunner(this._httpClient, addressOverride: addressOverride, allowedAddresses: allowedAddresses);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://allowed-host.com"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act & Assert - AddressOverride should also be validated against allowlist
        var ex = await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
        Assert.Contains("not allowed", ex.Message);
    }

    [Fact]
    public async Task ShouldRejectAddressOverrideWithDisallowedSchemeAsync()
    {
        // Arrange
        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);
        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var addressOverride = new Uri("http://insecure-host.com/");
        var sut = new GrpcOperationRunner(this._httpClient, addressOverride: addressOverride);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://safe-host.com"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act & Assert - AddressOverride with http should be rejected when only https is allowed
        var ex = await Assert.ThrowsAsync<KernelException>(() => sut.RunAsync(operation, arguments));
        Assert.Contains("scheme", ex.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ShouldRunOperationsWithSimpleDataContractAsync()
    {
        // Arrange

        //The byte array is copied from intercepted gRPC call to a local gPRC service created using this guide - https://learn.microsoft.com/en-us/aspnet/core/tutorials/grpc/grpc-start?view=aspnetcore-7.0&tabs=visual-studio
        //since there's no simple way to obtain/create serialized content of gRPC response.
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent([0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114]);
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", [new("name", 1, "TYPE_STRING")]);

        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", [new("message", 1, "TYPE_STRING")]);

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata)
        {
            Package = "greet",
            Address = "https://fake-random-test-host"
        };

        var arguments = new KernelArguments
        {
            { "payload", JsonSerializer.Serialize(new { name = "author" }) }
        };

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(result);

        var contentProperty = result["content"]?.ToString();
        Assert.NotNull(contentProperty);

        var jsonContent = JsonNode.Parse(contentProperty);
        Assert.NotNull(jsonContent);

        var messageProperty = jsonContent["message"]?.ToString();
        Assert.Equal("Hello author", messageProperty);

        var contentTypeProperty = result["contentType"]?.ToString();
        Assert.Equal("application/json; charset=utf-8", contentTypeProperty);

        //The byte array is copied from intercepted gRPC call to a local gPRC service created using this guide - https://learn.microsoft.com/en-us/aspnet/core/tutorials/grpc/grpc-start?view=aspnetcore-7.0&tabs=visual-studio
        //since there's no simple way to obtain/create serialized content of gRPC request.
        Assert.Equal(new byte[] { 0, 0, 0, 0, 8, 10, 6, 97, 117, 116, 104, 111, 114 }, this._httpMessageHandlerStub.RequestContent);
    }

    /// <summary>
    /// Disposes resources used by this class.
    /// </summary>
    public void Dispose()
    {
        this._httpMessageHandlerStub.Dispose();

        this._httpClient.Dispose();
    }

    private sealed class HttpMessageHandlerStub : DelegatingHandler
    {
        public HttpRequestHeaders? RequestHeaders { get; private set; }

        public HttpContentHeaders? ContentHeaders { get; private set; }

        public byte[]? RequestContent { get; private set; }

        public Uri? RequestUri { get; private set; }

        public HttpMethod? Method { get; private set; }

        public HttpResponseMessage ResponseToReturn { get; set; }

        public HttpMessageHandlerStub()
        {
            this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json)
            };
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.Method = request.Method;
            this.RequestUri = request.RequestUri;
            this.RequestHeaders = request.Headers;
            this.RequestContent = request.Content is null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken);
            this.ContentHeaders = request.Content?.Headers;

            return await Task.FromResult(this.ResponseToReturn);
        }
    }
}
