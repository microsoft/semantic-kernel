// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Xunit;

namespace SemanticKernel.Connectors.AssemblyAI.UnitTests.AudioToText;

/// <summary>
/// Unit tests for <see cref="AssemblyAIAudioToTextService"/> class.
/// </summary>
public sealed class AssemblyAIAudioToTextServiceExtensionsTests
{
    private const string ApiKey = "Test123";
    private const string Endpoint = "http://localhost:1234/";
    private const string ServiceId = "AssemblyAI";

    [Fact]
    public void AddServiceWithParameters()
    {
        // Arrange & Act
        var kernel = Kernel.CreateBuilder()
            .AddAssemblyAIAudioToText(
                apiKey: ApiKey,
                serviceId: ServiceId
            )
            .Build();

        // Assert
        AssertService(kernel);
    }

    private static void AssertService(
        Kernel kernel,
        string? endpoint = null
    )
    {
        var service = kernel.GetRequiredService<IAudioToTextService>();
        Assert.NotNull(service);
        Assert.IsType<AssemblyAIAudioToTextService>(service);

        service = kernel.GetRequiredService<IAudioToTextService>(ServiceId);
        Assert.NotNull(service);
        Assert.IsType<AssemblyAIAudioToTextService>(service);

        var aaiService = (AssemblyAIAudioToTextService)service;
        Assert.Equal(ApiKey, aaiService.ApiKey);
        Assert.NotNull(aaiService.HttpClient);
        if (endpoint != null)
        {
            Assert.NotNull(aaiService.HttpClient.BaseAddress);
            Assert.Equal(Endpoint, aaiService.HttpClient.BaseAddress!.ToString());
        }
    }
}
