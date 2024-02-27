// Copyright (c) Microsoft. All rights reserved.

using System;
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
    private static readonly TimeSpan s_pollingInterval = TimeSpan.FromMilliseconds(500);

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
        this.AssertService(kernel);
    }

    private void AssertService(
        Kernel kernel,
        string? endpoint = null,
        TimeSpan? pollingInterval = null
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

        if (pollingInterval != null)
        {
            Assert.Equal(s_pollingInterval, aaiService.PollingInterval);
        }
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
        configuration["PollingInterval"] = s_pollingInterval.ToString();

        // Act
        var kernel = Kernel.CreateBuilder()
            .AddAssemblyAIAudioToText(
                configuration,
                serviceId: ServiceId
            )
            .Build();

        // Assert
        this.AssertService(kernel, Endpoint, s_pollingInterval);
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
                    options.PollingInterval = s_pollingInterval;
                },
                serviceId: ServiceId
            )
            .Build();

        // Assert
        this.AssertService(kernel, Endpoint, s_pollingInterval);
    }
}
