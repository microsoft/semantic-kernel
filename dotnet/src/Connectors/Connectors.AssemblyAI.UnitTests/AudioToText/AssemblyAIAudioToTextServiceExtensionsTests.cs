// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Connectors.AssemblyAI;
using Xunit;

namespace SemanticKernel.Connectors.AssemblyAI.UnitTests.AudioToText;

/// <summary>
/// Unit tests for <see cref="AssemblyAIServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AssemblyAIAudioToTextServiceExtensionsTests
{
    private const string ApiKey = "Test123";
    private const string Endpoint = "http://localhost:1234/";
    private const string ServiceId = "AssemblyAI";

    [Fact]
    public void AddServiceToKernelBuilder()
    {
        // Arrange & Act
        var kernel = Kernel.CreateBuilder()
            .AddAssemblyAIAudioToText(
                apiKey: ApiKey,
                endpoint: Endpoint,
                serviceId: ServiceId
            )
            .Build();

        // Assert
        var service = kernel.GetRequiredService<IAudioToTextService>();
        Assert.NotNull(service);
        Assert.IsType<AssemblyAIAudioToTextService>(service);

        service = kernel.GetRequiredService<IAudioToTextService>(ServiceId);
        Assert.NotNull(service);
        Assert.IsType<AssemblyAIAudioToTextService>(service);

        var aaiService = (AssemblyAIAudioToTextService)service;
        Assert.Equal(ApiKey, aaiService.ApiKey);
        Assert.NotNull(aaiService.HttpClient);
        Assert.NotNull(aaiService.HttpClient.BaseAddress);
        Assert.Equal(Endpoint, aaiService.HttpClient.BaseAddress!.ToString());
    }

    [Fact]
    public void AddServiceToServiceCollection()
    {
        // Arrange & Act
        var services = new ServiceCollection();
        services.AddAssemblyAIAudioToText(
            apiKey: ApiKey,
            endpoint: Endpoint,
            serviceId: ServiceId
        );
        using var provider = services.BuildServiceProvider();

        // Assert
        var service = provider.GetRequiredKeyedService<IAudioToTextService>(ServiceId);
        Assert.NotNull(service);
        Assert.IsType<AssemblyAIAudioToTextService>(service);

        var aaiService = (AssemblyAIAudioToTextService)service;
        Assert.Equal(ApiKey, aaiService.ApiKey);
        Assert.NotNull(aaiService.HttpClient);
        Assert.NotNull(aaiService.HttpClient.BaseAddress);
        Assert.Equal(Endpoint, aaiService.HttpClient.BaseAddress!.ToString());
    }
}
