// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SKEXP0010

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Onnx;

public class OnnxRuntimeGenAIChatClientTests : BaseIntegrationTest
{
    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseKernelInvokeAsyncWithChatClient()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernelWithChatClient();

        var func = kernel.CreateFunctionFromPrompt("List the two planets after '{{$input}}', excluding moons, using bullet points.");

        // Act
        var result = await func.InvokeAsync(kernel, new() { ["input"] = "Jupiter" });

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Saturn", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Uranus", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseKernelInvokeStreamingAsyncWithChatClient()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernelWithChatClient();

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
    public async Task ItCanUseServiceGetResponseAsync()
    {
        using var chatClient = CreateChatClient();

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Where is the most famous fish market in Seattle, Washington, USA?")
        };

        var response = await chatClient.GetResponseAsync(messages);

        // Assert
        Assert.NotNull(response);
        Assert.Contains("Pike Place", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItCanUseServiceGetStreamingResponseAsync()
    {
        using var chatClient = CreateChatClient();

        var messages = new List<ChatMessage>
        {
            new(ChatRole.User, "Where is the most famous fish market in Seattle, Washington, USA?")
        };

        StringBuilder fullResult = new();

        await foreach (var update in chatClient.GetStreamingResponseAsync(messages))
        {
            fullResult.Append(update.Text);
        }

        // Assert
        Assert.Contains("Pike Place", fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    private static IChatClient CreateChatClient()
    {
        Assert.NotNull(Configuration.ModelPath);
        Assert.NotNull(Configuration.ModelId);

        var services = new ServiceCollection();
        services.AddOnnxRuntimeGenAIChatClient(Configuration.ModelId, Configuration.ModelPath);

        var serviceProvider = services.BuildServiceProvider();
        return serviceProvider.GetRequiredService<IChatClient>();
    }

    #region internals

    private Kernel CreateAndInitializeKernelWithChatClient(HttpClient? httpClient = null)
    {
        Assert.NotNull(Configuration.ModelPath);
        Assert.NotNull(Configuration.ModelId);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddOnnxRuntimeGenAIChatClient(
            modelId: Configuration.ModelId,
            modelPath: Configuration.ModelPath,
            serviceId: Configuration.ServiceId);

        return kernelBuilder.Build();
    }

    private static OnnxConfiguration Configuration => new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OnnxRuntimeGenAIChatClientTests>()
        .Build()
        .GetRequiredSection("Onnx")
        .Get<OnnxConfiguration>()!;

    #endregion
}
