// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Onnx;

public class OnnxRuntimeGenAIChatCompletionServiceTests : BaseIntegrationTest
{
    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseKernelInvokeAsyncAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var func = kernel.CreateFunctionFromPrompt("List the two planets after '{{$input}}', excluding moons, using bullet points.");

        // Act
        var result = await func.InvokeAsync(kernel, new() { ["input"] = "Jupiter" });

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Saturn", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Uranus", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseKernelInvokeStreamingAsyncAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var plugins = TestHelpers.ImportSamplePlugins(kernel, "ChatPlugin");

        StringBuilder fullResult = new();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        await foreach (var content in kernel.InvokeStreamingAsync<StreamingKernelContent>(plugins["ChatPlugin"]["Chat"], new() { ["input"] = prompt }))
        {
            fullResult.Append(content);
        }

        // Assert
        Assert.Contains("Pike Place", fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseServiceGetStreamingChatMessageContentsAsync()
    {
        using var chat = CreateService();

        ChatHistory history = [];
        history.AddUserMessage("Where is the most famous fish market in Seattle, Washington, USA?");

        StringBuilder fullResult = new();

        await foreach (var content in chat.GetStreamingChatMessageContentsAsync(history))
        {
            fullResult.Append(content);
        }

        // Assert
        Assert.Contains("Pike Place", fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseServiceGetChatMessageContentsAsync()
    {
        using var chat = CreateService();

        ChatHistory history = [];
        history.AddUserMessage("Where is the most famous fish market in Seattle, Washington, USA?");

        var content = await chat.GetChatMessageContentAsync(history);

        Assert.Contains("Pike Place", content.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    private static OnnxRuntimeGenAIChatCompletionService CreateService()
    {
        Assert.NotNull(Configuration.ModelPath);
        Assert.NotNull(Configuration.ModelId);

        return new OnnxRuntimeGenAIChatCompletionService(Configuration.ModelId, Configuration.ModelPath);
    }

    #region internals

    private Kernel CreateAndInitializeKernel(HttpClient? httpClient = null)
    {
        Assert.NotNull(Configuration.ModelPath);
        Assert.NotNull(Configuration.ModelId);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOnnxRuntimeGenAIChatCompletion(
            modelId: Configuration.ModelId,
            modelPath: Configuration.ModelPath,
            serviceId: Configuration.ServiceId);

        return kernelBuilder.Build();
    }

    private static OnnxConfiguration Configuration => new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OnnxRuntimeGenAIChatCompletionServiceTests>()
        .Build()
        .GetRequiredSection("Onnx")
        .Get<OnnxConfiguration>()!;

    #endregion
}
