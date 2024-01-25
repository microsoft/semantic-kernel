// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example78_RAG : BaseTest
{
    /// <summary>
    /// Shows how to use RAG pattern with ChatGPT Retrieval Plugin
    /// </summary>
    [Fact(Skip = "Requires hosted ChatGPT Retrieval Plugin and data store")]
    public async Task RAGWithChatGPTRetrievalPluginAsync()
    {
        var openApi = EmbeddedResource.ReadStream("chat-gpt-retrieval-plugin-open-api.yaml");

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey)
            .Build();

        await kernel.ImportPluginFromOpenApiAsync("ChatGPTRetrievalPlugin", openApi!, executionParameters: new(authCallback: async (request, cancellationToken) =>
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", TestConfiguration.ChatGPTRetrievalPlugin.Token);
        }));

        const string Query = "What is my budget for 2024?";
        const string Prompt = "{{search queries=$queries}} {{$query}}";

        var result = await kernel.InvokePromptAsync(Prompt, GetChatGPTRetrievalPluginArguments(Query));

        WriteLine(result);
    }

    public Example78_RAG(ITestOutputHelper output) : base(output)
    {
    }

    #region private

    private KernelArguments GetChatGPTRetrievalPluginArguments(string query)
    {
        return new()
        {
            ["query"] = query,
            ["queries"] = JsonSerializer.Serialize(new List<object> { new { query, top_k = 1 } }),
        };
    }

    #endregion
}
