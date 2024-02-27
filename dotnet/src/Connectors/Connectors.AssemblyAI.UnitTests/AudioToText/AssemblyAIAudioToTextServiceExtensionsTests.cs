// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Configuration.Memory;
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
                endpoint: Endpoint,
                serviceId: ServiceId
            )
            .Build();

        // Assert
        var service = kernel.GetRequiredService<IAudioToTextService>();
        this.AssertService(service);

        service = kernel.GetRequiredService<IAudioToTextService>(ServiceId);
        this.AssertService(service);
    }

    private void AssertService(IAudioToTextService service)
    {
        Assert.NotNull(service);
        Assert.IsType<AssemblyAIAudioToTextService>(service);

        var aaiService = (AssemblyAIAudioToTextService)service;
        Assert.Equal(ApiKey, aaiService.ApiKey);
        Assert.NotNull(aaiService.HttpClient);
        Assert.NotNull(aaiService.HttpClient.BaseAddress);
        Assert.Equal(Endpoint, aaiService.HttpClient.BaseAddress!.ToString());
    }

    [Fact]
    public void AddServiceWithConfiguration()
    {
        // Arrange
        using var configuration = new ConfigurationRoot([
            new MemoryConfigurationProvider(new MemoryConfigurationSource())
        ]);
        configuration["ApiKey"] = ApiKey;
        configuration["Endpoint"] = Endpoint;

        // Act
        var kernel = Kernel.CreateBuilder()
            .AddAssemblyAIAudioToText(
                configuration,
                serviceId: ServiceId
            )
            .Build();

        // Assert
        var service = kernel.GetRequiredService<IAudioToTextService>();
        this.AssertService(service);

        service = kernel.GetRequiredService<IAudioToTextService>(ServiceId);
        this.AssertService(service);
    }

    [Fact]
    public void AddServiceWithLambda()
    {
        // Arrange & Act
        var kernel = Kernel.CreateBuilder()
            .AddAssemblyAIAudioToText(
                options =>
                {
                    options.ApiKey = ApiKey;
                    options.Endpoint = Endpoint;
                },
                serviceId: ServiceId
            )
            .Build();

        // Assert
        var service = kernel.GetRequiredService<IAudioToTextService>();
        this.AssertService(service);

        service = kernel.GetRequiredService<IAudioToTextService>(ServiceId);
        this.AssertService(service);
    }
}
