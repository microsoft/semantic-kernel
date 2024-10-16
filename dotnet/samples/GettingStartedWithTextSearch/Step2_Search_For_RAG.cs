// Copyright (c) Microsoft. All rights reserved.
using System.Text.RegularExpressions;
using HtmlAgilityPack;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace GettingStartedWithTextSearch;

/// <summary>
/// This example shows how to use <see cref="ITextSearch"/> for Retrieval Augmented Generation (RAG).
/// </summary>
public class Step2_Search_For_RAG(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from a <see cref="BingTextSearch"/> and use it to
    /// add grounding context to a prompt.
    /// </summary>
    [Fact]
    public async Task RagWithTextSearchAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a text search using Bing search
        ITextSearch textSearch = this.UseBingSearch ?
            new BingTextSearch(
                apiKey: TestConfiguration.Bing.ApiKey) :
            new GoogleTextSearch(
                searchEngineId: TestConfiguration.Google.SearchEngineId,
                apiKey: TestConfiguration.Google.ApiKey);

        // Build a text search plugin with web search and add to the kernel
        var searchPlugin = textSearch.CreateWithSearch("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        var prompt = "{{SearchPlugin.Search $query}}. {{$query}}";
        KernelArguments arguments = new() { { "query", query } };
        Console.WriteLine(await kernel.InvokePromptAsync(prompt, arguments));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch"/> and use it to
    /// add grounding context to a Handlebars prompt and include citations in the response.
    /// </summary>
    [Fact]
    public async Task RagWithBingTextSearchIncludingCitationsAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a text search using Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = textSearch.CreateWithGetTextSearchResults("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = """
            {{#with (SearchPlugin-GetTextSearchResults query)}}  
              {{#each this}}  
                Name: {{Name}}
                Value: {{Value}}
                Link: {{Link}}
                -----------------
              {{/each}}  
            {{/with}}  

            {{query}}

            Include citations to the relevant information where it is referenced in the response.
            """;
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch"/> and use it to
    /// add grounding context to a Handlebars prompt and include citations in the response.
    /// </summary>
    [Fact]
    public async Task RagWithBingTextSearchIncludingTimeStampedCitationsAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a text search using Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = textSearch.CreateWithGetSearchResults("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = """
            {{#with (SearchPlugin-GetSearchResults query)}}  
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
            """;
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch"/> and use it to
    /// add grounding context to a Handlebars prompt that includes results from the Microsoft Developer Blogs site.
    /// </summary>
    [Fact]
    public async Task RagWithBingTextSearchUsingDevBlogsSiteAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a text search using Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Create a filter to search only the Microsoft Developer Blogs site
        var filter = new TextSearchFilter().Equality("site", "devblogs.microsoft.com");
        var searchOptions = new TextSearchOptions() { Filter = filter };

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = KernelPluginFactory.CreateFromFunctions(
            "SearchPlugin", "Search Microsoft Developer Blogs site only",
            [textSearch.CreateGetTextSearchResults(searchOptions: searchOptions)]);
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = """
            {{#with (SearchPlugin-GetTextSearchResults query)}}  
              {{#each this}}  
                Name: {{Name}}
                Value: {{Value}}
                Link: {{Link}}
                -----------------
              {{/each}}  
            {{/with}}  

            {{query}}

            Include citations to the relevant information where it is referenced in the response.
            """;
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch"/> and use it to
    /// add grounding context to a Handlebars prompt that include results for the specified web site.
    /// </summary>
    [Fact]
    public async Task RagWithBingTextSearchUsingCustomSiteAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a text search using Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var options = new KernelFunctionFromMethodOptions()
        {
            FunctionName = "GetSiteResults",
            Description = "Perform a search for content related to the specified query and optionally from the specified domain.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("top") { Description = "Number of results", IsRequired = false, DefaultValue = 5 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
                new KernelParameterMetadata("site") { Description = "Only return results from this domain", IsRequired = false },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<string>) },
        };
        var searchPlugin = KernelPluginFactory.CreateFromFunctions("SearchPlugin", "Search specified site", [textSearch.CreateGetTextSearchResults(options)]);
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = """
            {{#with (SearchPlugin-GetSiteResults query)}}  
              {{#each this}}  
                Name: {{Name}}
                Value: {{Value}}
                Link: {{Link}}
                -----------------
              {{/each}}  
            {{/with}}  

            {{query}}

            Only include results from techcommunity.microsoft.com. 
            Include citations to the relevant information where it is referenced in the response.
            """;
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="ITextSearch"/> and use it to
    /// add grounding context to a Handlebars prompt that include full web pages.
    /// </summary>
    [Fact]
    public async Task RagWithBingTextSearchUsingFullPagesAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId, // Requires a large context window e.g. gpt-4o or gpt-4o-mini 
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a text search using Bing search
        var textSearch = new TextSearchWithFullValues(new BingTextSearch(new(TestConfiguration.Bing.ApiKey)));

        // Create a filter to search only the Microsoft Developer Blogs site
        var filter = new TextSearchFilter().Equality("site", "devblogs.microsoft.com");
        var searchOptions = new TextSearchOptions() { Filter = filter };

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = KernelPluginFactory.CreateFromFunctions(
            "SearchPlugin", "Search Microsoft Developer Blogs site only",
            [textSearch.CreateGetTextSearchResults(searchOptions: searchOptions)]);
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        var query = "What is the Semantic Kernel?";
        string promptTemplate = """
            {{#with (SearchPlugin-GetTextSearchResults query)}}  
              {{#each this}}  
                Name: {{Name}}
                Value: {{Value}}
                Link: {{Link}}
                -----------------
              {{/each}}  
            {{/with}}  

            {{query}}

            Include citations to the relevant information where it is referenced in the response.
            """;
        KernelArguments arguments = new() { { "query", query } };
        HandlebarsPromptTemplateFactory promptTemplateFactory = new();
        Console.WriteLine(await kernel.InvokePromptAsync(
            promptTemplate,
            arguments,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: promptTemplateFactory
        ));
    }
}

/// <summary>
/// Wraps a <see cref="ITextSearch"/> to provide full web pages as search results.
/// </summary>
public partial class TextSearchWithFullValues(ITextSearch searchDelegate) : ITextSearch
{
    /// <inheritdoc/>
    public Task<KernelSearchResults<object>> GetSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return searchDelegate.GetSearchResultsAsync(query, searchOptions, cancellationToken);
    }

    /// <inheritdoc/>
    public async Task<KernelSearchResults<TextSearchResult>> GetTextSearchResultsAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        var results = await searchDelegate.GetTextSearchResultsAsync(query, searchOptions, cancellationToken);

        var resultList = new List<TextSearchResult>();

        using HttpClient client = new();
        await foreach (var item in results.Results.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            string? value = item.Value;
            try
            {
                if (item.Link is not null)
                {
                    value = await client.GetStringAsync(new Uri(item.Link), cancellationToken);
                    value = ConvertHtmlToPlainText(value);
                }
            }
            catch (HttpRequestException)
            {
            }

            resultList.Add(new(value) { Name = item.Name, Link = item.Link });
        }

        return new KernelSearchResults<TextSearchResult>(resultList.ToAsyncEnumerable<TextSearchResult>(), results.TotalCount, results.Metadata);
    }

    /// <inheritdoc/>
    public Task<KernelSearchResults<string>> SearchAsync(string query, TextSearchOptions? searchOptions = null, CancellationToken cancellationToken = default)
    {
        return searchDelegate.SearchAsync(query, searchOptions, cancellationToken);
    }

    /// <summary>
    /// Convert HTML to plain text.
    /// </summary>
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
