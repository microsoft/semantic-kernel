// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using Microsoft.SemanticKernel;
using OpenAI;

namespace ChatCompletion;

public sealed class OpenAI_CustomClient(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        Assert.NotNull(TestConfiguration.OpenAI.ChatModelId);
        Assert.NotNull(TestConfiguration.OpenAI.ApiKey);

        Console.WriteLine("======== Using a custom OpenAI client ========");

        // Create an HttpClient and include your custom header(s)
        using var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.Add("My-Custom-Header", "My Custom Value");

        // Configure AzureOpenAIClient to use the customized HttpClient
        var clientOptions = new OpenAIClientOptions
        {
            Transport = new HttpClientPipelineTransport(httpClient),
            NetworkTimeout = TimeSpan.FromSeconds(30),
            RetryPolicy = new ClientRetryPolicy()
        };

        var customClient = new OpenAIClient(new ApiKeyCredential(TestConfiguration.OpenAI.ApiKey), clientOptions);

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, customClient)
            .Build();

        // Load semantic plugin defined with prompt templates
        string folder = RepoFiles.SamplePluginsPath();

        kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "FunPlugin"));

        // Run
        var result = await kernel.InvokeAsync(
            kernel.Plugins["FunPlugin"]["Excuses"],
            new() { ["input"] = "I have no homework" }
        );
        Console.WriteLine(result.GetValue<string>());

        httpClient.Dispose();
    }
}
