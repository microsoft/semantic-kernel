// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace Search;

/// <summary>
/// This example shows how to perform function calling with an <see cref="ITextSearch"/>.
/// </summary>
public class Bing_FunctionCallingWithTextSearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="BingTextSearch"/> and use it with
    /// function calling to have the LLM include grounding context in it's response.
    /// </summary>
    [Fact]
    public async Task FunctionCallingWithBingTextSearchAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a search service with Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = textSearch.CreateWithSearch("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        KernelArguments arguments = new(settings);
        Console.WriteLine(await kernel.InvokePromptAsync("What is the Semantic Kernel?", arguments));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="BingTextSearch"/> and use it with
    /// function calling and have the LLM include links in the final response.
    /// </summary>
    [Fact]
    public async Task FunctionCallingWithBingTextSearchIncludingCitationsAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a search service with Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = textSearch.CreateWithGetTextSearchResults("SearchPlugin");
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        KernelArguments arguments = new(settings);
        Console.WriteLine(await kernel.InvokePromptAsync("What is the Semantic Kernel? Include citations to the relevant information where it is referenced in the response.", arguments));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="BingTextSearch"/> and use it with
    /// function calling to have the LLM include grounding context from the Microsoft Dev Blogs site in it's response.
    /// </summary>
    [Fact]
    public async Task FunctionCallingWithBingTextSearchUsingDevBlogsSiteAsync()

    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a search service with Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var basicFilter = new BasicFilterOptions().Equality("site", "devblogs.microsoft.com");
        var searchOptions = new TextSearchOptions() { BasicFilter = basicFilter };
        var searchPlugin = KernelPluginFactory.CreateFromFunctions(
            "SearchPlugin", "Search Microsoft Developer Blogs site only",
            [textSearch.CreateGetTextSearchResults(searchOptions: searchOptions)]);
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        KernelArguments arguments = new(settings);
        Console.WriteLine(await kernel.InvokePromptAsync("What is the Semantic Kernel? Include citations to the relevant information where it is referenced in the response.", arguments));
    }

    /// <summary>
    /// Show how to create a default <see cref="KernelPlugin"/> from an <see cref="BingTextSearch"/> and use it with
    /// function calling to have the LLM include grounding context from the Microsoft Dev Blogs site in it's response.
    /// </summary>
    [Fact]
    public async Task FunctionCallingWithBingTextSearchUsingSiteArgumentAsync()
    {
        // Create a kernel with OpenAI chat completion
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        // Create a search service with Bing search
        var textSearch = new BingTextSearch(new(TestConfiguration.Bing.ApiKey));

        // Build a text search plugin with Bing search and add to the kernel
        var searchPlugin = KernelPluginFactory.CreateFromFunctions("SearchPlugin", "Search specified site", [CreateSearchBySite(textSearch)]);
        kernel.Plugins.Add(searchPlugin);

        // Invoke prompt and use text search plugin to provide grounding information
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        KernelArguments arguments = new(settings);
        Console.WriteLine(await kernel.InvokePromptAsync("What is the Semantic Kernel? Only include results from learn.microsoft.com. Include citations to the relevant information where it is referenced in the response.", arguments));
    }

    private static KernelFunction CreateSearchBySite(BingTextSearch textSearch, BasicFilterOptions? basicFilter = null, MapSearchResultToString? mapToString = null)
    {
        async Task<IEnumerable<object>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            arguments.TryGetValue("count", out var count);
            arguments.TryGetValue("skip", out var skip);
            arguments.TryGetValue("site", out var site);
            BasicFilterOptions? basicFilter = null;
            if (string.IsNullOrEmpty(site?.ToString()))
            {
                basicFilter = new BasicFilterOptions().Equality("site", site?.ToString()!);
            }
            TextSearchOptions searchOptions = new()
            {
                Count = (count as int?) ?? 2,
                Offset = (skip as int?) ?? 0,
                BasicFilter = basicFilter
            };

            var result = await textSearch.GetSearchResultsAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
            return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        var options = new KernelFunctionFromMethodOptions()
        {
            FunctionName = "Search",
            Description = "Perform a search for content related to the specified query and optionally from the specified domain.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
                new KernelParameterMetadata("site") { Description = "Only return results from this domain", IsRequired = false, DefaultValue = 2 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<string>) },
        };

        return KernelFunctionFactory.CreateFromMethod(SearchAsync, options);
    }
}
