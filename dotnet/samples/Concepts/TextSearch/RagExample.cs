// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using HtmlAgilityPack;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.Search;

namespace TextSearch;

/// <summary>
/// This example shows how to perform RAG with an <see cref="ITextSearch{T}"/>.
/// </summary>
public sealed partial class RagExample(ITestOutputHelper output) : BaseTest(output)
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

        // Create a text search using the Bing search service
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = textSearch.CreateKernelPluginWithTextSearch("SearchPlugin");
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

        // Create a text search using the Bing search service
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = textSearch.CreateKernelPluginWithGetSearchResults("SearchPlugin");
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

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to
    /// add grounding context to a Handlebars prompt and include citations in the response.
    /// </summary>
    [Fact]
    public async Task HandlebarRagWithBingTextSearchWithCitationsAsync()
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

        // Create a text search using the Bing search service
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = textSearch.CreateKernelPluginWithGetSearchResults("SearchPlugin");
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

Include citations to the relevant information where it is referenced in the response.
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
        The Semantic Kernel (SK) is a lightweight and powerful SDK developed by Microsoft that integrates Large Language Models (LLMs) such as OpenAI, Azure OpenAI, and Hugging Face with traditional programming languages like C#, Python, and Java ([GitHub](https://github.com/microsoft/semantic-kernel)). It facilitates the combination of natural language processing capabilities with pre-existing APIs and code, enabling developers to add large language capabilities to their applications swiftly ([What It Is and Why It Matters](https://techcommunity.microsoft.com/t5/microsoft-developer-community/semantic-kernel-what-it-is-and-why-it-matters/ba-p/3877022)).

        The Semantic Kernel serves as a middleware that translates the AI model's requests into function calls, effectively bridging the gap between semantic functions (LLM tasks) and native functions (traditional computer code) ([InfoWorld](https://www.infoworld.com/article/2338321/semantic-kernel-a-bridge-between-large-language-models-and-your-code.html)). It also enables the automatic orchestration and execution of tasks using natural language prompting across multiple languages and platforms ([Hello, Semantic Kernel!](https://devblogs.microsoft.com/semantic-kernel/hello-world/)).

        In addition to its core capabilities, Semantic Kernel supports advanced functionalities like prompt templating, chaining, and planning, which allow developers to create intricate workflows tailored to specific use cases ([Architecting AI Apps](https://devblogs.microsoft.com/semantic-kernel/architecting-ai-apps-with-semantic-kernel/)).

        By describing your existing code to the AI models, Semantic Kernel effectively marshals the request to the appropriate function, returns results back to the LLM, and enables the AI agent to generate a final response ([Quickly Start](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)). This process brings unparalleled productivity and new experiences to application users ([Hello, Semantic Kernel!](https://devblogs.microsoft.com/semantic-kernel/hello-world/)).

        The Semantic Kernel is an indispensable tool for developers aiming to build advanced AI applications by seamlessly integrating large language models with traditional programming frameworks ([Comprehensive Guide](https://gregdziedzic.com/understanding-semantic-kernel-a-comprehensive-guide/)).
         */
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to
    /// add grounding context to a Handlebars prompt and include citations in the response.
    /// </summary>
    [Fact]
    public async Task HandlebarRagWithBingTextSearchWithTimeStampedCitationsAsync()
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

        // Create a text search using the Bing search service
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = textSearch.CreateKernelPluginWithGetBingWebPages("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = @"
{{#with (SearchPlugin-GetBingWebPages query)}}  
  {{#each this}}  
    Name: {{Name}}
    Snippet: {{Snippet}}
    Link: {{DisplayUrl}}
    Date Last Crawled: {{DateLastCrawled}}
    -----------------
  {{/each}}  
{{/with}}  

{{query}}

Include citations to and the date of the relevant information where it is referenced in the response.
"; //  and order the relevant information so the most recent comes first
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));

        /*
        Semantic Kernel is an open-source development kit designed to facilitate the integration of advanced AI models into existing C#, Python, or Java codebases. It serves as an efficient middleware that enables rapid delivery of enterprise-grade AI solutions (Microsoft Learn, 2024-08-14).

        One of the standout features of Semantic Kernel is its lightweight SDK, which allows developers to blend conventional programming languages with Large Language Model (LLM) AI capabilities through prompt templating, chaining, and planning (Semantic Kernel Blog, 2024-08-10).

        This AI SDK uses natural language prompting to create and execute semantic AI tasks across multiple languages and platforms, offering developers a simple yet powerful programming model to add large language capabilities to their applications in a matter of minutes (Microsoft Developer Community, 2024-08-13).

        Semantic Kernel also leverages function calling—a native feature of most LLMs—enabling the models to request specific functions to fulfill user requests, thereby streamlining the planning process (Microsoft Learn, 2024-08-14).

        The toolkit is versatile and extends support to multiple programming environments. For instance, Semantic Kernel for Java is compatible with Java 8 and above, making it accessible to a wide range of Java developers (Semantic Kernel Blog, 2024-08-14).

        Additionally, Sketching an architecture with Semantic Kernel can simplify business automation using models from platforms such as OpenAI, Azure OpenAI, and Hugging Face (Semantic Kernel Blog, 2024-08-14).

        For .NET developers, Semantic Kernel is highly recommended for working with AI in .NET applications, offering a comprehensive guide on incorporating Semantic Kernel into projects and understanding its core concepts (Microsoft Learn, 2024-08-14).

        Last but not least, Semantic Kernel has an extension for Visual Studio Code that facilitates the design and testing of semantic functions, enabling developers to efficiently integrate and test AI models with their existing data (GitHub, 2024-08-14).

        References:
        - Microsoft Learn. "Introduction to Semantic Kernel." Last crawled: 2024-08-14.
        - Semantic Kernel Blog. "Hello, Semantic Kernel!" Last crawled: 2024-08-10.
        - Microsoft Developer Community. "Semantic Kernel: What It Is and Why It Matters." Last crawled: 2024-08-13.
        - Microsoft Learn. "How to quickly start with Semantic Kernel." Last crawled: 2024-08-14.
        - Semantic Kernel Blog. "Introducing Semantic Kernel for Java." Last crawled: 2024-08-14.
        - Microsoft Learn. "Semantic Kernel overview for .NET." Last crawled: 2024-08-14.
        - GitHub. "microsoft/semantic-kernel." Last crawled: 2024-08-14.
         */
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch{T}"/> and use it to
    /// add grounding context to a Handlebars prompt that include full web pages.
    /// </summary>
    [Fact]
    public async Task HandlebarRagWithBingTextSearchWithFullWebPagesAsync()
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

        // Create a text search using the Bing search service
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search service and add to the kernel
        var searchPlugin = KernelPluginFactory.CreateFromFunctions("SearchPlugin", null, [CreateGetFullWebPages(textSearch)]);
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = @"
{{#with (SearchPlugin-GetFullWebPages query)}}  
  {{#each this}}  
    Name: {{Name}}
    Value: {{Value}}
    Link: {{Link}}
    -----------------
  {{/each}}  
{{/with}}  

{{query}}

Include citations to the relevant information where it is referenced in the response.
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
        The Semantic Kernel (SK) is a lightweight, open-source development kit designed to facilitate the integration of advanced AI models into applications. It allows developers to build AI agents and incorporate large language models (LLMs) into C#, Python, or Java codebases. Here are some key aspects of the Semantic Kernel:

        1. **Middleware for Rapid Development**: The Semantic Kernel acts as an efficient middleware, enabling rapid delivery of enterprise-grade AI solutions. It supports prompts and existing APIs to perform actions, so developers can automate business processes ([Microsoft Learn - Introduction to Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview)).

        2. **Integration Capabilities**: It combines the capabilities of traditional programming languages with the latest AI models through prompt templating, chaining, and planning capabilities. This enables developers to build novel, AI-driven experiences ([Hello, Semantic Kernel!](https://devblogs.microsoft.com/semantic-kernel/hello-world)).

        3. **Extensible and Modular**: The Semantic Kernel is highly flexible and modular, allowing developers to add their existing code as plugins. It uses OpenAPI specifications, facilitating the sharing of extensions within development teams. Additionally, any existing chat-based APIs can be expanded to support other modalities like voice and video ([Introduction to Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview)).

        4. **AI Services and Plugins**: The kernel orchestrates various AI services and plugins to perform complex tasks. It manages dependencies, selects the best AI service, builds and sends prompts, handles responses, and logs operations, all from a centralized place ([Understanding the kernel in Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/kernel)).

        5. **Support for Enterprise Applications**: Semantic Kernel is built with enterprise needs in mind, offering security-enhancing capabilities like telemetry support and filters, ensuring responsible AI delivery. It also allows logging and status updates to enhance observability and compliance ([Architecting AI Apps with Semantic Kernel](https://devblogs.microsoft.com/semantic-kernel/architecting-ai-apps-with-semantic-kernel)).

        6. **Native and Hybrid Plugins**: Plugins can encapsulate either native code or AI prompts, providing a seamless way for AI agents to interact with various services, APIs, and perform tasks like web searches, customer relationship management, and document editing ([Understanding the kernel in Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/concepts/kernel)).

        By leveraging these features, the Semantic Kernel serves as a powerful toolset for developers looking to enhance their applications with cutting-edge AI capabilities, all while maintaining flexibility and ease of integration. For more details and to access the Semantic Kernel SDK, visit the [GitHub repository](https://github.com/microsoft/semantic-kernel).
        */
    }

    private static KernelFunction CreateGetFullWebPages(ITextSearch<BingWebPage> textSearch, BasicFilterOptions? basicFilter = null)
    {
        async Task<IEnumerable<TextSearchResult>> GetFullWebPagesAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            arguments.TryGetValue("count", out var count);
            arguments.TryGetValue("skip", out var skip);
            SearchOptions searchOptions = new()
            {
                Count = (count as int?) ?? 2,
                Offset = (skip as int?) ?? 0,
                BasicFilter = basicFilter
            };

            var result = await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
            var resultList = new List<TextSearchResult>();

            using HttpClient client = new();
            await foreach (var item in result.Results.WithCancellation(cancellationToken).ConfigureAwait(false))
            {
                string? value = item.Snippet;
                try
                {
                    if (item.Url is not null)
                    {
                        value = await client.GetStringAsync(new Uri(item.Url), cancellationToken);
                        value = ConvertHtmlToPlainText(value);
                    }
                }
                catch (HttpRequestException)
                {
                }

                resultList.Add(new() { Name = item.Name, Value = value, Link = item.Url });
            }

            return resultList;
        }

        var options = new KernelFunctionFromMethodOptions()
        {
            FunctionName = "GetFullWebPages",
            Description = "Perform a search for content related to the specified query. The search will return the name, full web page content and link for the related content.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
                new KernelParameterMetadata("site") { Description = "Only return results from this domain", IsRequired = false, DefaultValue = 2 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<string>) },
        };

        return KernelFunctionFactory.CreateFromMethod(GetFullWebPagesAsync, options);
    }

    private static string ConvertHtmlToPlainText(string html)
    {
        HtmlDocument doc = new();
        doc.LoadHtml(html);

        string text = doc.DocumentNode.InnerText;
        text = MyRegex().Replace(text, " "); // Remove unnecessary whitespace  
        return text.Trim();
    }

    [GeneratedRegex(@"\s+")]
    private static partial Regex MyRegex();
}
