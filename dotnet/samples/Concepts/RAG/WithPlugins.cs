// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Text.Json;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.InMemory;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using OpenAI;
using Resources;

namespace RAG;

public class WithPlugins(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RAGWithCustomPluginAsync()
    {
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        kernel.ImportPluginFromType<CustomPlugin>();

        var result = await kernel.InvokePromptAsync("{{search 'budget by year'}} What is my budget for 2024?");

        Console.WriteLine(result);
    }

    /// <summary>
    /// Shows how to use RAG pattern with <see cref="InMemoryVectorStore"/>.
    /// </summary>
    [Fact]
    public async Task RAGWithInMemoryVectorStoreAndPluginAsync()
    {
        var textEmbeddingGenerator = new OpenAIClient(TestConfiguration.OpenAI.ApiKey)
            .GetEmbeddingClient(TestConfiguration.OpenAI.EmbeddingModelId)
            .AsIEmbeddingGenerator();

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(TestConfiguration.OpenAI.ChatModelId, TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create the collection and add data
        var vectorStore = new InMemoryVectorStore(new() { EmbeddingGenerator = textEmbeddingGenerator });
        var collection = vectorStore.GetCollection<string, FinanceInfo>("finances");
        await collection.CreateCollectionAsync();
        string[] budgetInfo =
        {
            "The budget for 2020 is EUR 100 000",
            "The budget for 2021 is EUR 120 000",
            "The budget for 2022 is EUR 150 000",
            "The budget for 2023 is EUR 200 000",
            "The budget for 2024 is EUR 364 000"
        };
        var records = budgetInfo.Select((input, index) => new FinanceInfo { Key = index.ToString(), Text = input });
        await collection.UpsertAsync(records);

        // Add the collection to the kernel as a plugin.
        var textSearch = new VectorStoreTextSearch<FinanceInfo>(collection);
        kernel.Plugins.Add(textSearch.CreateWithSearch("FinanceSearch", "Can search for budget information"));

        // Invoke the kernel, using the plugin from within the prompt.
        KernelArguments arguments = new() { { "query", "What is my budget for 2024?" } };
        var result = await kernel.InvokePromptAsync(
            "{{FinanceSearch-Search query}} {{query}}",
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: new HandlebarsPromptTemplateFactory());

        Console.WriteLine(result);
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

        Console.WriteLine(result);
    }

    #region Custom Plugin

    private sealed class CustomPlugin
    {
        [KernelFunction]
        public async Task<string> SearchAsync(string query)
        {
            // Here will be a call to vector DB, return example result for demo purposes
            return "Year Budget 2020 100,000 2021 120,000 2022 150,000 2023 200,000 2024 364,000";
        }
    }

    private sealed class FinanceInfo
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [TextSearchResultValue]
        [VectorStoreRecordData]
        public string Text { get; set; } = string.Empty;

        [VectorStoreRecordVector(1536)]
        public string Embedding => this.Text;
    }

    #endregion Custom Plugin
}
