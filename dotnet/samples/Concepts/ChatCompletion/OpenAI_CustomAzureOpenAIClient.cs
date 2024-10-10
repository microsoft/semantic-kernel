// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;
using Azure;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;

namespace ChatCompletion;

public sealed class OpenAI_CustomAzureOpenAIClient(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== Using a custom OpenAI client ========");

        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string deploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || deploymentName is null || apiKey is null)
        {
            Console.WriteLine("Azure OpenAI credentials not found. Skipping example.");
            return;
        }

        // Create an HttpClient and include your custom header(s)
        var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.Add("My-Custom-Header", "My Custom Value");

        // Configure AzureOpenAIClient to use the customized HttpClient
        var clientOptions = new AzureOpenAIClientOptions
        {
            Transport = new HttpClientPipelineTransport(httpClient),
        };
        var openAIClient = new AzureOpenAIClient(new Uri(endpoint), new AzureKeyCredential(apiKey), clientOptions);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.AddAzureOpenAIChatCompletion(deploymentName, openAIClient);
        Kernel kernel = builder.Build();

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
