// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI.CustomClient.Moderation;

public sealed class OpenAIHttpRequestFactoryTests
{
    [Fact]
    public void ItReturnsRequestWithOrganizationHeader()
    {
        // Arrange
        string? organization = "sampleOrganization";
        var sut = CreateOpenAIHttpRequestFactory(organization: organization);

        // Act
        var request = sut.CreatePost(new object(), new Uri("https://example.com"));

        // Assert
        var header = request.Headers.GetValues("OpenAI-Organization").SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(organization, header);
    }

    [Fact]
    public void ItReturnsRequestWithUserAgentHeader()
    {
        // Arrange
        var sut = CreateOpenAIHttpRequestFactory();

        // Act
        var request = sut.CreatePost(new object(), new Uri("https://example.com"));

        // Assert
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, request.Headers.UserAgent.ToString());
    }

    [Fact]
    public void ItReturnsRequestWithSemanticKernelVersionHeader()
    {
        // Arrange
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(OpenAIHttpRequestFactory));
        var sut = CreateOpenAIHttpRequestFactory();

        // Act
        var request = sut.CreatePost(new object(), new Uri("https://example.com"));

        // Assert
        var header = request.Headers.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    [Fact]
    public void ItReturnsRequestWithBearerAuthorizationHeader()
    {
        // Arrange
        string apiKey = "sampleApiKey";
        var sut = CreateOpenAIHttpRequestFactory(apiKey: apiKey);

        // Act
        var request = sut.CreatePost(new object(), new Uri("https://example.com"));

        // Assert
        Assert.NotNull(request.Headers.Authorization);
        Assert.Equal("Bearer", request.Headers.Authorization.Scheme);
        Assert.Equal(apiKey, request.Headers.Authorization.Parameter);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("    ")]
    public void ItThrowsArgumentExceptionWhenApiKeyIsInvalid(string? key)
    {
        // Act & Assert
        Assert.ThrowsAny<ArgumentException>(() => CreateOpenAIHttpRequestFactory(apiKey: key!));
    }

    [Fact]
    public void ItReturnsRequestWithData()
    {
        // Arrange
        var data = new object();
        var sut = CreateOpenAIHttpRequestFactory();

        // Act
        var request = sut.CreatePost(data, new Uri("https://example.com"));

        // Assert
        Assert.NotNull(request.Content);
    }

    [Fact]
    public void ItReturnsRequestWithPostMethod()
    {
        // Arrange
        var sut = CreateOpenAIHttpRequestFactory();

        // Act
        var request = sut.CreatePost(new object(), new Uri("https://example.com"));

        // Assert
        Assert.Equal(HttpMethod.Post, request.Method);
    }

    [Fact]
    public void ItReturnsRequestWithEndpoint()
    {
        // Arrange
        var endpoint = new Uri("http://example.com");
        var sut = CreateOpenAIHttpRequestFactory();

        // Act
        var request = sut.CreatePost(new object(), endpoint);

        // Assert
        Assert.Equal(endpoint, request.RequestUri);
    }

    private static OpenAIHttpRequestFactory CreateOpenAIHttpRequestFactory(string apiKey = "apiKey", string? organization = null)
    {
        return new OpenAIHttpRequestFactory(apiKey: apiKey, organization: organization);
    }
}
