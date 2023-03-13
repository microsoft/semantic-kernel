// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernelTests;
public class HttpClientFactoryTests
{
    [Fact]
    [System.Diagnostics.CodeAnalysis.SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "The handler is disposed by HttpClient itself.")]
    public void ItCreatesHttpClient()
    {
        //Arrange
        using var factory = new HttpClientFactory();

        //Act
        var httpClient = factory.Create(new HttpClientHandler(), true);

        //Assert
        Assert.NotNull(httpClient);
        httpClient.Dispose();
    }
}
