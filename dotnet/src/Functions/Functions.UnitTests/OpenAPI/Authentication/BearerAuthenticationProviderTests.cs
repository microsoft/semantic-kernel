// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Authentication;

public class BearerAuthenticationProviderTests
{
    [Fact]
    public async Task AuthenticateRequestAsyncSucceedsAsync()
    {
        // Arrange
        var token = Guid.NewGuid().ToString();
        using var request = new HttpRequestMessage();

        var target = new BearerAuthenticationProvider(() => Task.FromResult(token));

        // Act
        await target.AuthenticateRequestAsync(request);

        // Assert
        Assert.Equal("Bearer", request.Headers.Authorization?.Scheme);
        Assert.Equal(token, request.Headers.Authorization?.Parameter);
    }
}
