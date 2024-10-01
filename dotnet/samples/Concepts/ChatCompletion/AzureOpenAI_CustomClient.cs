// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;

namespace ChatCompletion;

public sealed class AzureOpenAI_CustomClient(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Using a custom AzureOpenAI client ========");

        Assert.NotNull(TestConfiguration.AzureOpenAI.Endpoint);
        Assert.NotNull(TestConfiguration.AzureOpenAI.ChatDeploymentName);
        Assert.NotNull(TestConfiguration.AzureOpenAI.ApiKey);

        // Create an HttpClient and include your custom header(s)
        var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.Add("My-Custom-Header", "My Custom Value");

        // Configure AzureOpenAIClient to use the customized HttpClient
        var clientOptions = new AzureOpenAIClientOptions
        {
            Transport = new HttpClientPipelineTransport(httpClient),
            NetworkTimeout = TimeSpan.FromSeconds(30),
            RetryPolicy = new ClientRetryPolicy()
        };

        var customClient = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), new ApiKeyCredential(TestConfiguration.AzureOpenAI.ApiKey), clientOptions);

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(TestConfiguration.AzureOpenAI.ChatDeploymentName, customClient)
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
