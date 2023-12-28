#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests;

public class GeminiServiceCollectionExtensionsTests
{
    [Fact]
    public void GeminiTextGenerationServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGeminiTextGeneration("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<GeminiTextGenerationService>(textGenerationService);
    }

    [Fact]
    public void GeminiTextGenerationServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGeminiTextGeneration("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<GeminiTextGenerationService>(textGenerationService);
    }
}
