// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using Kernel.CreateBuilder().

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;

namespace KernelExamples;

public class BuildingKernel(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public void BuildKernelWithAzureChatCompletion()
    {
        // KernelBuilder provides a simple way to configure a Kernel. This constructs a kernel
        // with logging and an Azure OpenAI chat completion service configured.
        Kernel kernel1 = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();
    }

    [Fact]
    public void BuildKernelWithPlugins()
    {
        // Plugins may also be configured via the corresponding Plugins property.
        var builder = Kernel.CreateBuilder();
        builder.Plugins.AddFromType<HttpPlugin>();
        Kernel kernel3 = builder.Build();
    }
}
