// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to perform RAG with an <see cref="ITextSearch{T}"/>.
/// </summary>
public sealed class RagExample(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to
    /// add grounding context to a prompt.
    /// </summary>
    [Fact]
    public async Task RagWithBingTextSearchAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        HttpClient httpClient = new(handler);

        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey,
                httpClient: httpClient);
        Kernel kernel = kernelBuilder.Build();

        // Create a search service with Bing search service
        var searchService = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = TextSearchKernelPluginFactory.CreateFromTextSearch<string>(searchService, "SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        KernelArguments arguments = new() { { "query", query } };
        Console.WriteLine(await kernel.InvokePromptAsync("{{SearchPlugin.Search $query}}. {{$query}}", arguments));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to
    /// add grounding context to a Handlebars prompt.
    /// </summary>
    [Fact]
    public async Task HandlebarRagWithBingTextSearchAsync()
    {
        // Create a logging handler to output HTTP requests and responses
        LoggingHandler handler = new(new HttpClientHandler(), this.Output);
        HttpClient httpClient = new(handler);

        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey,
                httpClient: httpClient);
        Kernel kernel = kernelBuilder.Build();

        // Create a search service with Bing search service
        var searchService = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = TextSearchKernelPluginFactory.CreateFromTextSearch<TextSearchResult>(searchService, "SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = @"
{{#with (SearchPlugin-GetSearchResults query)}}  
  {{#each this}}  
    Name: {{Name}}
    Value: {{Value}}
    Link: {{Link}}
    -----------------
  {{/each}}  
{{/with}}  

{{query}}

Include the link to the relevant information in the response.
";
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));

        /*
         Semantic Kernel is a lightweight, open-source development kit that allows developers to easily build AI agents and integrate the latest AI models into C#, Python, or Java codebases. It serves as efficient middleware, enabling the rapid delivery of enterprise-grade solutions. It leverages function calling—a native feature of most large language models (LLMs)—to provide planning and can be used to add large language capabilities to applications through natural language prompting and execution of semantic tasks.
    
         For more information, you can visit:
         - The overview from Microsoft Learn: [Introduction to Semantic Kernel | Microsoft Learn](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
         - Detailed explanation about its purpose and significance: [Semantic Kernel: What It Is and Why It Matters](https://techcommunity.microsoft.com/t5/microsoft-developer-community/semantic-kernel-what-it-is-and-why-it-matters/ba-p/3877022)
         */
    }
}
