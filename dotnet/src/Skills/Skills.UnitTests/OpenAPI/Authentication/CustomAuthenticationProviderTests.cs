// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI.Authentication;

public class CustomAuthenticationProviderTests
{
    [Fact]
    public async Task AuthenticateRequestAsyncSucceedsAsync()
    {
        // Arrange
        var header = "X-MyHeader";
        var value = Guid.NewGuid().ToString();

        using var request = new HttpRequestMessage();

        var target = new CustomAuthenticationProvider(() => Task.FromResult(header), () => Task.FromResult(value));

        // Act
        await target.AuthenticateRequestAsync(request);

        // Assert
        Assert.True(request.Headers.Contains(header));
        Assert.Equal(request.Headers.GetValues(header).FirstOrDefault(), value);
    }
}
