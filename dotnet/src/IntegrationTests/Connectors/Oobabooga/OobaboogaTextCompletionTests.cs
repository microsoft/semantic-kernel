// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Oobabooga;

/// <summary>
/// Integration tests for <see cref=" OobaboogaTextCompletion"/>.
/// </summary>
public sealed class OobaboogaTextCompletionTests
{
    private const string Endpoint = "http://localhost";
    private const int BlockingPort = 5000;
    private const int StreamingPort = 5005;

    private readonly IConfigurationRoot _configuration;

    public OobaboogaTextCompletionTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .Build();
    }

    private const string Input = "My name is";

    [Fact(Skip = "This test is for manual verification.")]
    public async Task OobaboogaLocalTextCompletionAsync()
    {
        using var oobaboogaLocal = new OobaboogaTextCompletion(new Uri(Endpoint), BlockingPort, StreamingPort);

        // Act
        var localResponse = await oobaboogaLocal.CompleteAsync(Input, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 5,
            TopP = 0.1,
        });

        // Assert
        Assert.NotNull(localResponse);
        Assert.StartsWith(Input, localResponse.Trim(), StringComparison.Ordinal);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public void OobaboogaLocalTextCompletionStreamingAsync()
    {
        using var oobaboogaLocal = new OobaboogaTextCompletion(new Uri(Endpoint), BlockingPort, StreamingPort);

        // Act
        var localResponse = oobaboogaLocal.CompleteStreamAsync(Input, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 5,
            TopP = 0.1,
        });

        // Assert
        Assert.NotNull(localResponse);
        var resultsMerged = localResponse.ToEnumerable().Aggregate("", (s, s1) => s + s1).Trim();
        Assert.StartsWith(Input, resultsMerged, StringComparison.Ordinal);
    }
}
