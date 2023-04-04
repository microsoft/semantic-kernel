// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Microsoft.SemanticKernel.Skills.OpenAPI.Rest;
using Moq;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI;

public class RestApiOperationRunnerTests
{
    [Fact]
    public async Task ItCanRunCrudOperationWithJsonPayloadSuccessfullyAsync()
    {
        //Arrange
        using var httpMessageHandlerStub = new HttpMessageHandlerStub();
        using var httpClient = new HttpClient(httpMessageHandlerStub);
        var authCallbackMock = new Mock<AuthenticateRequestAsyncCallback>();
        var sut = new RestApiOperationRunner(httpClient, authCallbackMock.Object);

        List<RestApiOperationPayloadProperty> payloadProperties = new()
        {
            new("value", "string", true, new List<RestApiOperationPayloadProperty>() , "fake-value-description"),
            new("attributes", "object", false, new List<RestApiOperationPayloadProperty>()
            {
                new("enabled", "boolean", false, new List<RestApiOperationPayloadProperty>() , "fake-enabled-description"),
            })
        };

        var payload = new RestApiOperationPayload(MediaTypeNames.Application.Json, payloadProperties);

        var operation = new RestApiOperation(
            "fake-id",
            "https://fake-random-test-host",
            "fake-path",
            HttpMethod.Post,
            "fake-description",
            new List<RestApiOperationParameter>(),
            payload
         );

        var arguments = new Dictionary<string, string>();
        arguments.Add("value", "fake-value");
        arguments.Add("enabled", "true");

        //Act
        await sut.RunAsync(operation, arguments);

        //Assert
        Assert.NotNull(httpMessageHandlerStub.RequestUri);
        Assert.Equal("https://fake-random-test-host/fake-path", httpMessageHandlerStub.RequestUri.AbsoluteUri);

        Assert.Equal(HttpMethod.Post, httpMessageHandlerStub.Method);

        Assert.NotNull(httpMessageHandlerStub.ContentHeaders);
        Assert.Contains(httpMessageHandlerStub.ContentHeaders, h => h.Key == "Content-Type" && h.Value.Contains("application/json; charset=utf-8"));

        var messageContent = httpMessageHandlerStub.RequestContent;
        Assert.NotNull(messageContent);
        Assert.True(messageContent.Any());

        var deserializedPayload = JsonNode.Parse(new MemoryStream(messageContent));
        Assert.NotNull(deserializedPayload);

        var valueProperty = deserializedPayload["value"]?.ToString();
        Assert.Equal("fake-value", valueProperty);

        var attributesProperty = deserializedPayload["attributes"];
        Assert.NotNull(attributesProperty);

        var enabledProperty = attributesProperty["enabled"]?.AsValue();
        Assert.NotNull(enabledProperty);
        Assert.Equal("true", enabledProperty.ToString());

        authCallbackMock.Verify(x => x(It.IsAny<HttpRequestMessage>()), Times.Once);
    }



    private class HttpMessageHandlerStub : DelegatingHandler
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
