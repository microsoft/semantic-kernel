// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Chroma;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Resources;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example78_RAG : BaseTest
{
    /// <summary>
    /// Shows how to use RAG pattern with <see cref="TextMemoryPlugin"/>.
    /// </summary>
    [Fact(Skip = "Requires Chroma server up and running")]
    public async Task RAGWithTextMemoryPluginAsync()
    {
        var memory = new MemoryBuilder()
            .WithMemoryStore(new ChromaMemoryStore("http://localhost:8000"))
            .WithOpenAITextEmbeddingGeneration(TestConfiguration.OpenAI.EmbeddingModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        kernel.ImportPluginFromObject(new TextMemoryPlugin(memory));

        var result = await kernel.InvokePromptAsync("{{recall 'budget by year' collection='finances'}} What is my budget for 2024?");

        WriteLine(result);
    }

    /// <summary>
    /// Shows how to use RAG pattern with ChatGPT Retrieval Plugin.
    /// </summary>
    [Fact(Skip = "Requires ChatGPT Retrieval Plugin and selected vector DB server up and running")]
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

        var arguments = new KernelArguments
        {
            ["query"] = Query,
            ["queries"] = JsonSerializer.Serialize(new List<object> { new { query = Query, top_k = 1 } }),
        };

        var result = await kernel.InvokeAsync(function, arguments);

        WriteLine(result);
    }

    public Example78_RAG(ITestOutputHelper output) : base(output)
    {
    }
}
