// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Provides extension methods for interacting with <see cref="ITextSearch"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class TextSearchExtensions
{
    #region KernelPlugin factory methods
    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `Search` which
    /// will return a <see cref="IEnumerable{String}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelPlugin CreateWithSearch(this ITextSearch textSearch, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateSearch()]);
    }

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetSearchResults` which
    /// will return a <see cref="IEnumerable{TextSearchResult}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetTextSearchResults operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelPlugin CreateWithGetTextSearchResults(this ITextSearch textSearch, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetTextSearchResults()]);
    }

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetSearchResults` which
    /// will return a <see cref="IEnumerable{TextSearchResult}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetSearchResults operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelPlugin CreateWithGetSearchResults(this ITextSearch textSearch, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetSearchResults()]);
    }
    #endregion

    #region KernelFunction factory methods
    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelFunction CreateSearch(this ITextSearch textSearch, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<string>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Count = GetArgumentValue(arguments, parameters, "count", 2),
                Offset = GetArgumentValue(arguments, parameters, "skip", 0),
                Filter = CreateBasicFilter(options, arguments)
            };

            var result = await textSearch.SearchAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
            var resultList = await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
            return resultList;
        }

        options ??= DefaultSearchMethodOptions();
        return KernelFunctionFactory.CreateFromMethod(
                SearchAsync,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelFunction CreateGetTextSearchResults(this ITextSearch textSearch, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<TextSearchResult>> GetTextSearchResultAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Count = GetArgumentValue(arguments, parameters, "count", 2),
                Offset = GetArgumentValue(arguments, parameters, "skip", 0),
                Filter = CreateBasicFilter(options, arguments)
            };

            var result = await textSearch.GetTextSearchResultsAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
            return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultGetTextSearchResultsMethodOptions();
        return KernelFunctionFactory.CreateFromMethod(
                GetTextSearchResultAsync,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelFunction CreateGetSearchResults(this ITextSearch textSearch, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<object>> GetSearchResultAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Count = GetArgumentValue(arguments, parameters, "count", 2),
                Offset = GetArgumentValue(arguments, parameters, "skip", 0),
                Filter = CreateBasicFilter(options, arguments)
            };

            var result = await textSearch.GetSearchResultsAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
            return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultGetSearchResultsMethodOptions();
        return KernelFunctionFactory.CreateFromMethod(
                GetSearchResultAsync,
                options);
    }
    #endregion

    #region private
    /// <summary>
    /// Get the argument value from <see cref="KernelArguments"/> or users default value from
    /// <see cref="KernelReturnParameterMetadata"/> or default to the provided value.
    /// </summary>
    /// <param name="arguments">KernelArguments instance.</param>
    /// <param name="parameters">List of KernelReturnParameterMetadata.</param>
    /// <param name="name">Name of the argument.</param>
    /// <param name="defaultValue">Default value of the argument.</param>
    private static int GetArgumentValue(KernelArguments arguments, IReadOnlyList<KernelParameterMetadata> parameters, string name, int defaultValue)
    {
        if (arguments.TryGetValue(name, out var value) && value is int argument)
        {
            return argument;
        }

        value = parameters.FirstOrDefault(parameter => parameter.Name == name)?.DefaultValue;
        if (value is int metadataDefault)
        {
            return metadataDefault;
        }

        return defaultValue;
    }

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions DefaultSearchMethodOptions() =>
        new()
        {
            FunctionName = "Search",
            Description = "Perform a search for content related to the specified query and return string results",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<string>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions DefaultGetTextSearchResultsMethodOptions() =>
        new()
        {
            FunctionName = "GetTextSearchResults",
            Description = "Perform a search for content related to the specified query. The search will return the name, value and link for the related content.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions DefaultGetSearchResultsMethodOptions() =>
        new()
        {
            FunctionName = "GetSearchResults",
            Description = "Perform a search for content related to the specified query.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };

    /// <summary>
    /// Create a <see cref="TextSearchFilter" /> for the search based on any additional parameters included in the <see cref="KernelFunctionFromMethodOptions"/>
    /// </summary>
    /// <param name="options">Kernel function method options.</param>
    /// <param name="arguments">Kernel arguments.</param>
    private static TextSearchFilter? CreateBasicFilter(KernelFunctionFromMethodOptions? options, KernelArguments arguments)
    {
        if (options?.Parameters is null)
        {
            return null;
        }

        TextSearchFilter? filter = null;
        foreach (var parameter in options.Parameters)
        {
            // treat non standard parameters as equality filter clauses
            if (!parameter.Name.Equals("query", System.StringComparison.Ordinal) &&
                !parameter.Name.Equals("count", System.StringComparison.Ordinal) &&
                !parameter.Name.Equals("skip", System.StringComparison.Ordinal))
            {
                if (arguments.TryGetValue(parameter.Name, out var value) && value is not null)
                {
                    filter ??= new TextSearchFilter();
                    filter.Equality(parameter.Name, value);
                }
            }
        }

        return filter;
    }
    #endregion
}
