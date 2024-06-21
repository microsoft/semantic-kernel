// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

public partial class ClientCoreTests
{
    [Fact]
    public async Task ItGetEmbeddingsAsyncReturnsEmptyWhenProvidedDataIsEmpty()
    {
        // Arrange
        var clientCore = new ClientCore("model", "apikey");

        // Act
        var result = await clientCore.GetEmbeddingsAsync([], null, null, CancellationToken.None);

        // Assert
        Assert.Empty(result);
    }
}
