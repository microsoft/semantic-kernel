// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Google.Apis.Http;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Google;

namespace Search;

/// <summary>
/// This example shows how to create and use a <see cref="GoogleTextSearch"/>.
/// </summary>
public class Google_TextSearch(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearch"/> and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingGoogleTextSearchAsync()
    {
        // Create an ITextSearch instance using Google search
        var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = TestConfiguration.Google.ApiKey, HttpClientFactory = new CustomHttpClientFactory(this.Output) },
            searchEngineId: TestConfiguration.Google.SearchEngineId);

        var query = "What is the Semantic Kernel?";

        // Search and return results as string items
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 4, Skip = 0 });
        Console.WriteLine("——— String Results ———\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new() { Top = 4, Skip = 4 });
        Console.WriteLine("\n——— Text Search Results ———\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Search and return results as Google.Apis.CustomSearchAPI.v1.Data.Result items
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new() { Top = 4, Skip = 8 });
        Console.WriteLine("\n——— Google Web Page Results ———\n");
        await foreach (Google.Apis.CustomSearchAPI.v1.Data.Result result in fullResults.Results)
        {
            Console.WriteLine($"Title:       {result.Title}");
            Console.WriteLine($"Snippet:     {result.Snippet}");
            Console.WriteLine($"Link:        {result.Link}");
            Console.WriteLine($"DisplayLink: {result.DisplayLink}");
            Console.WriteLine($"Kind:        {result.Kind}");
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }
    }

    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingGoogleTextSearchWithACustomMapperAsync()
    {
        // Create an ITextSearch instance using Google search
        var textSearch = new GoogleTextSearch(
            searchEngineId: TestConfiguration.Google.SearchEngineId,
            apiKey: TestConfiguration.Google.ApiKey,
            options: new() { StringMapper = new TestTextSearchStringMapper() });

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new() { Top = 2, Skip = 0 });
        Console.WriteLine("--- Serialized JSON Results ---");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }
    }

    /// <summary>
    /// Show how to create a <see cref="GoogleTextSearch"/> with a custom mapper and use it to perform a text search.
    /// </summary>
    [Fact]
    public async Task UsingGoogleTextSearchWithASiteSearchFilterAsync()
    {
        // Create an ITextSearch instance using Google search
        var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = TestConfiguration.Google.ApiKey, HttpClientFactory = new CustomHttpClientFactory(this.Output) },
            searchEngineId: TestConfiguration.Google.SearchEngineId);

        var query = "What is the Semantic Kernel?";

        // Search with TextSearchResult textResult type
        TextSearchOptions searchOptions = new() { Top = 4, Skip = 0, Filter = new TextSearchFilter().Equality("siteSearch", "devblogs.microsoft.com") };
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, searchOptions);
        Console.WriteLine("--- Microsoft Developer Blogs Results ---");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine(result.Link);
            Console.WriteLine(new string('-', HorizontalRuleLength));
        }
    }

    #region private
    private const int HorizontalRuleLength = 80;

    /// <summary>
    /// Test mapper which converts an arbitrary search result to a string using JSON serialization.
    /// </summary>
    private sealed class TestTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            return JsonSerializer.Serialize(result);
        }
    }

    /// <summary>
    /// Implementation of <see cref="ConfigurableMessageHandler"/> which logs HTTP responses.
    /// </summary>
    private sealed class LoggingConfigurableMessageHandler(HttpMessageHandler innerHandler, ITestOutputHelper output) : ConfigurableMessageHandler(innerHandler)
    {
        private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { WriteIndented = true };

        private readonly ITestOutputHelper _output = output;

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Log the request details
            if (request.Content is not null)
            {
                var content = await request.Content.ReadAsStringAsync(cancellationToken);
                this._output.WriteLine("=== REQUEST ===");
                try
                {
                    string formattedContent = JsonSerializer.Serialize(JsonSerializer.Deserialize<JsonElement>(content), s_jsonSerializerOptions);
                    this._output.WriteLine(formattedContent);
                }
                catch (JsonException)
                {
                    this._output.WriteLine(content);
                }
                this._output.WriteLine(string.Empty);
            }

            // Call the next handler in the pipeline
            var response = await base.SendAsync(request, cancellationToken);

            if (response.Content is not null)
            {
                // Log the response details
                var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
                this._output.WriteLine("=== RESPONSE ===");
                this._output.WriteLine(responseContent);
                this._output.WriteLine(string.Empty);
            }

            return response;
        }
    }

    /// <summary>
    /// Implementation of <see cref="Google.Apis.Http.IHttpClientFactory"/> which uses the <see cref="LoggingConfigurableMessageHandler"/>.
    /// </summary>
    private sealed class CustomHttpClientFactory(ITestOutputHelper output) : Google.Apis.Http.IHttpClientFactory
    {
        private readonly ITestOutputHelper _output = output;

        public ConfigurableHttpClient CreateHttpClient(CreateHttpClientArgs args)
        {
            ConfigurableMessageHandler messageHandler = new LoggingConfigurableMessageHandler(new HttpClientHandler(), this._output);
            var configurableHttpClient = new ConfigurableHttpClient(messageHandler);
            return configurableHttpClient;
        }
    }
    #endregion
}
