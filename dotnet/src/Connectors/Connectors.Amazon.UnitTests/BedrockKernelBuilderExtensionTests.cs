// Copyright (c) Microsoft. All rights reserved.

using Connectors.Amazon.Extensions;
using Connectors.Amazon.Services;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace Connectors.Amazon.UnitTests;

public class BedrockKernelBuilderExtensionTests
{
    [Fact]
    public void AddBedrockTextGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddBedrockTextGenerationService("amazon.titan-text-premier-v1:0");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<BedrockTextGenerationService>(service);
    }

    [Fact]
    public void AddBedrockChatCompletionCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<BedrockChatCompletionService>(service);
    }
}
