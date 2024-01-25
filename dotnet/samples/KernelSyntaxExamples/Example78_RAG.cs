// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Chroma;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example78_RAG : BaseTest
{
    /// <summary>
    /// Shows how to use RAG pattern with ChatGPT Retrieval Plugin.
    /// </summary>
    [Fact(Skip = "Requires hosted ChatGPT Retrieval Plugin and memory store")]
    public async Task RAGWithChatGPTRetrievalPluginAsync()
    {
        var openApi = EmbeddedResource.ReadStream("chat-gpt-retrieval-plugin-open-api.yaml");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        await kernel.ImportPluginFromOpenApiAsync("ChatGPTRetrievalPlugin", openApi!, executionParameters: new(authCallback: async (request, cancellationToken) =>
        {
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", TestConfiguration.ChatGPTRetrievalPlugin.Token);
        }));

        const string Query = "What is my budget for 2024?";
        var function = KernelFunctionFactory.CreateFromPrompt("{{search queries=$queries}} {{$query}}");

        var result = await kernel.InvokeAsync(function, GetChatGPTRetrievalPluginArguments(Query));

        WriteLine(result);
    }

    /// <summary>
    /// Shows how to use RAG pattern with kernel.
    /// </summary>
    [Fact(Skip = "Requires hosted Chroma memory store")]
    public async Task RAGWithKernelAsync()
    {
        var builder = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .AddOpenAITextEmbeddingGeneration(TestConfiguration.OpenAI.EmbeddingModelId, TestConfiguration.OpenAI.ApiKey);

        builder.Services.AddSingleton<IMemoryStore>(new ChromaMemoryStore("http://localhost:8000"));
        builder.Services.AddSingleton<ISemanticTextMemory, SemanticTextMemory>();

        var kernel = builder.Build();

        var settings = new OpenAIPromptExecutionSettings { Temperature = 0.5, MemoryConfig = new("finances") };

        var result = await kernel.InvokePromptAsync("What is my budget for 2024?", new(settings));

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
