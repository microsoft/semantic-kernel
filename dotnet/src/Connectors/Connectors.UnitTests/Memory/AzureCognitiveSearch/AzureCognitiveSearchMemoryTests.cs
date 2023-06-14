// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.Core;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.AzureCognitiveSearch;

/// <summary>
/// Unit tests for <see cref="AzureCognitiveSearchMemory"/> class.
/// </summary>
public sealed class AzureCognitiveSearchMemoryTests : IDisposable
{
    private HttpMessageHandlerStub messageHandlerStub;
    private HttpClient httpClient;

    public AzureCognitiveSearchMemoryTests()
    {
        this.messageHandlerStub = new HttpMessageHandlerStub();

        this.httpClient = new HttpClient(this.messageHandlerStub, false);
    }

    [Fact]
    public async Task CustomHttpClientProvidedToFirstConstructorShouldBeUsed()
    {
        //Arrange
        var sut = new AzureCognitiveSearchMemory("https://fake-random-test-host/fake-path", "fake-api-key", this.httpClient);

        //Act
        await sut.GetAsync("fake-collection", "fake-query");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path/indexes('fake-collection')", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task CustomHttpClientProvidedToSecondConstructorShouldBeUsed()
    {
        //Arrange
        var credentials = DelegatedTokenCredential.Create((_, __) => new AccessToken("fake-access-token", DateTimeOffset.UtcNow.AddMinutes(15)));

        var sut = new AzureCognitiveSearchMemory("https://fake-random-test-host/fake-path", credentials, this.httpClient);

        //Act
        await sut.GetAsync("fake-collection", "fake-key");

        //Assert
        Assert.StartsWith("https://fake-random-test-host/fake-path/indexes('fake-collection')", this.messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose()
    {
        this.httpClient.Dispose();
        this.messageHandlerStub.Dispose();
    }
}
