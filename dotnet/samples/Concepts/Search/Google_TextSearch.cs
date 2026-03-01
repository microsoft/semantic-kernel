// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable CS0618 // Obsolete TextSearchOptions/TextSearchFilter

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
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new TextSearchOptions { Top = 4, Skip = 0 });
        Console.WriteLine("——— String Results ———\n");
        await foreach (string result in stringResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Search and return results as TextSearchResult items
        KernelSearchResults<TextSearchResult> textResults = await textSearch.GetTextSearchResultsAsync(query, new TextSearchOptions { Top = 4, Skip = 4 });
        Console.WriteLine("\n——— Text Search Results ———\n");
        await foreach (TextSearchResult result in textResults.Results)
        {
            Console.WriteLine($"Name:  {result.Name}");
            Console.WriteLine($"Value: {result.Value}");
            Console.WriteLine($"Link:  {result.Link}");
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Search and return results as Google.Apis.CustomSearchAPI.v1.Data.Result items
        KernelSearchResults<object> fullResults = await textSearch.GetSearchResultsAsync(query, new TextSearchOptions { Top = 4, Skip = 8 });
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
        KernelSearchResults<string> stringResults = await textSearch.SearchAsync(query, new TextSearchOptions { Top = 2, Skip = 0 });
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

    /// <summary>
    /// Show how to use enhanced LINQ filtering with GoogleTextSearch including Contains, NOT, FileType, and compound AND expressions.
    /// </summary>
    [Fact]
    public async Task UsingGoogleTextSearchWithEnhancedLinqFilteringAsync()
    {
        // Create an ITextSearch<GoogleWebPage> instance using Google search
        var textSearch = new GoogleTextSearch(
            initializer: new() { ApiKey = TestConfiguration.Google.ApiKey, HttpClientFactory = new CustomHttpClientFactory(this.Output) },
            searchEngineId: TestConfiguration.Google.SearchEngineId);

        var query = "Semantic Kernel AI";

        // Example 1: Simple equality filtering
        Console.WriteLine("——— Example 1: Equality Filter (DisplayLink) ———\n");
        var equalityOptions = new TextSearchOptions<GoogleWebPage>
        {
            Top = 2,
            Skip = 0,
            Filter = page => page.DisplayLink == "microsoft.com"
        };
        var equalityResults = await textSearch.SearchAsync(query, equalityOptions);
        await foreach (string result in equalityResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Example 2: Contains filtering
        Console.WriteLine("\n——— Example 2: Contains Filter (Title) ———\n");
        var containsOptions = new TextSearchOptions<GoogleWebPage>
        {
            Top = 2,
            Skip = 0,
            Filter = page => page.Title != null && page.Title.Contains("AI")
        };
        var containsResults = await textSearch.SearchAsync(query, containsOptions);
        await foreach (string result in containsResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Example 3: NOT Contains filtering (exclusion)
        Console.WriteLine("\n——— Example 3: NOT Contains Filter (Exclude 'deprecated') ———\n");
        var notContainsOptions = new TextSearchOptions<GoogleWebPage>
        {
            Top = 2,
            Skip = 0,
            Filter = page => page.Title != null && !page.Title.Contains("deprecated")
        };
        var notContainsResults = await textSearch.SearchAsync(query, notContainsOptions);
        await foreach (string result in notContainsResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Example 4: FileFormat filtering
        Console.WriteLine("\n——— Example 4: FileFormat Filter (PDF files) ———\n");
        var fileFormatOptions = new TextSearchOptions<GoogleWebPage>
        {
            Top = 2,
            Skip = 0,
            Filter = page => page.FileFormat == "pdf"
        };
        var fileFormatResults = await textSearch.SearchAsync(query, fileFormatOptions);
        await foreach (string result in fileFormatResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Example 5: Compound AND filtering (multiple conditions)
        Console.WriteLine("\n——— Example 5: Compound AND Filter (Title + Site) ———\n");
        var compoundOptions = new TextSearchOptions<GoogleWebPage>
        {
            Top = 2,
            Skip = 0,
            Filter = page => page.Title != null && page.Title.Contains("Semantic") &&
                           page.DisplayLink != null && page.DisplayLink.Contains("microsoft")
        };
        var compoundResults = await textSearch.SearchAsync(query, compoundOptions);
        await foreach (string result in compoundResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
        }

        // Example 6: Complex compound filtering (equality + contains + exclusion)
        Console.WriteLine("\n——— Example 6: Complex Compound Filter (FileFormat + Contains + NOT Contains) ———\n");
        var complexOptions = new TextSearchOptions<GoogleWebPage>
        {
            Top = 2,
            Skip = 0,
            Filter = page => page.FileFormat == "pdf" &&
                           page.Title != null && page.Title.Contains("AI") &&
                           page.Snippet != null && !page.Snippet.Contains("deprecated")
        };
        var complexResults = await textSearch.SearchAsync(query, complexOptions);
        await foreach (string result in complexResults.Results)
        {
            Console.WriteLine(result);
            Console.WriteLine(new string('—', HorizontalRuleLength));
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
                    string formattedContent = JsonSerializer.Serialize(JsonElement.Parse(content), s_jsonSerializerOptions);
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
