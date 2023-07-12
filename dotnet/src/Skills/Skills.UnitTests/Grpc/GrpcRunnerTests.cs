// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.Grpc;
using Microsoft.SemanticKernel.Skills.Grpc.Model;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.Grpc;

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
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent(new byte[] { 0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114 });
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", new List<GrpcOperationDataContractTypeFiled>() { new("name", 1, "TYPE_STRING") });

        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", new List<GrpcOperationDataContractTypeFiled>() { new("message", 1, "TYPE_STRING") });

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata);
        operation.Package = "greet";
        operation.Address = "https://fake-random-test-host";

        var arguments = new Dictionary<string, string>();
        arguments.Add("payload", JsonSerializer.Serialize(new { name = "author" }));

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/greet.Greeter/SayHello", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldUseAddressOverrideFromArgumentsAsync()
    {
        // Arrange
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent(new byte[] { 0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114 });
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", new List<GrpcOperationDataContractTypeFiled>() { new("name", 1, "TYPE_STRING") });

        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", new List<GrpcOperationDataContractTypeFiled>() { new("message", 1, "TYPE_STRING") });

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata);
        operation.Package = "greet";
        operation.Address = "https://fake-random-test-host";

        var arguments = new Dictionary<string, string>();
        arguments.Add("payload", JsonSerializer.Serialize(new { name = "author" }));
        arguments.Add("address", "https://fake-random-test-host-from-args");

        // Act
        var result = await sut.RunAsync(operation, arguments);

        // Assert
        Assert.NotNull(this._httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host-from-args/greet.Greeter/SayHello", this._httpMessageHandlerStub.RequestUri.AbsoluteUri);
    }

    [Fact]
    public async Task ShouldRunOperationsWithSimpleDataContractAsync()
    {
        // Arrange

        //The byte array is copied from intercepted gRPC call to a local gPRC service created using this guide - https://learn.microsoft.com/en-us/aspnet/core/tutorials/grpc/grpc-start?view=aspnetcore-7.0&tabs=visual-studio
        //since there's no simple way to obtain/create serialized content of gRPC response.
        this._httpMessageHandlerStub.ResponseToReturn.Content = new ByteArrayContent(new byte[] { 0, 0, 0, 0, 14, 10, 12, 72, 101, 108, 108, 111, 32, 97, 117, 116, 104, 111, 114 });
        this._httpMessageHandlerStub.ResponseToReturn.Version = new Version(2, 0);
        this._httpMessageHandlerStub.ResponseToReturn.Content.Headers.Add("Content-Type", "application/grpc");
        this._httpMessageHandlerStub.ResponseToReturn.TrailingHeaders.Add("grpc-status", "0");

        var requestMetadata = new GrpcOperationDataContractType("greet.HelloRequest", new List<GrpcOperationDataContractTypeFiled>() { new("name", 1, "TYPE_STRING") });

        var responseMetadata = new GrpcOperationDataContractType("greet.HelloReply", new List<GrpcOperationDataContractTypeFiled>() { new("message", 1, "TYPE_STRING") });

        var sut = new GrpcOperationRunner(this._httpClient);

        var operation = new GrpcOperation("Greeter", "SayHello", requestMetadata, responseMetadata);
        operation.Package = "greet";
        operation.Address = "https://fake-random-test-host";

        var arguments = new Dictionary<string, string>();
        arguments.Add("payload", JsonSerializer.Serialize(new { name = "author" }));

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
            this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK);
            this.ResponseToReturn.Content = new StringContent("{}", Encoding.UTF8, MediaTypeNames.Application.Json);
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.Method = request.Method;
            this.RequestUri = request.RequestUri;
            this.RequestHeaders = request.Headers;
            this.RequestContent = request.Content == null ? null : await request.Content.ReadAsByteArrayAsync(cancellationToken);
            this.ContentHeaders = request.Content?.Headers;

            return await Task.FromResult(this.ResponseToReturn);
        }
    }
}
