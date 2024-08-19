// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Provides extension methods for interacting with <see cref="ITextSearch{T}"/> and related types.
/// </summary>
public static class TextSearchExtensions
{
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
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateKernelPluginWithTextSearch(this ITextSearch<string> textSearch, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateTextSearch()]);
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
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateKernelPluginWithGetSearchResults(this ITextSearch<TextSearchResult> textSearch, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetSearchResults()]);
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <param name="mapToString"></param>
    /// <returns></returns>
    public static KernelFunction CreateTextSearch(this ITextSearch<string> textSearch, BasicFilterOptions? basicFilter = null, MapSearchResultToString? mapToString = null)
    {
        return textSearch.DefaultSearch(basicFilter, mapToString).CreateKernelFunction();
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <returns></returns>
    public static KernelFunction CreateGetSearchResults(this ITextSearch<TextSearchResult> textSearch, BasicFilterOptions? basicFilter = null)
    {
        return textSearch.DefaultGetSearchResults(basicFilter).CreateKernelFunction();
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <param name="mapToString"></param>
    /// <returns></returns>
    private static KernelFunctionFromTextSearchOptions DefaultSearch(this ITextSearch<string> textSearch, BasicFilterOptions? basicFilter = null, MapSearchResultToString? mapToString = null)
    {
        async Task<IEnumerable<string>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
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
                    Count = (count as int?) ?? GetDefaultValue(parameters, "count", 2),
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0),
                    BasicFilter = basicFilter
                };

                var result = await textSearch.SearchAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                var resultList = await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
                return MapToStrings(resultList, mapToString);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        return new()
        {
            Delegate = SearchAsync,
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
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <returns></returns>
    private static KernelFunctionFromTextSearchOptions DefaultGetSearchResults(this ITextSearch<TextSearchResult> textSearch, BasicFilterOptions? basicFilter = null)
    {
        async Task<IEnumerable<TextSearchResult>> GetSearchResultsAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
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
                    Count = (count as int?) ?? GetDefaultValue(parameters, "count", 2),
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0),
                    BasicFilter = basicFilter
                };

                var result = await textSearch.SearchAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        return new()
        {
            Delegate = GetSearchResultsAsync,
            FunctionName = "GetSearchResults",
            Description = "Perform a search for content related to the specified query. The search will return the name, value and link for the related content.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results to skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };
    }

    #region private

    private static List<string> MapToStrings(IEnumerable<object> resultList, MapSearchResultToString? mapToString = null)
    {
        mapToString ??= DefaultMapSearchResultToString;

        return resultList.Select(result => mapToString(result)).ToList();
    }

    /// <summary>
    /// TODO
    /// </summary>
    private static string DefaultMapSearchResultToString(object result)
    {
        if (result is string stringValue)
        {
            return stringValue;
        }
        return JsonSerializer.Serialize(result);
    }

    /// <summary>
    /// TODO
    /// </summary>
    private static int GetDefaultValue(IReadOnlyList<KernelParameterMetadata> parameters, string name, int defaultValue)
    {
        var value = parameters.FirstOrDefault(parameter => parameter.Name == name)?.DefaultValue;
        return value is int intValue ? intValue : defaultValue;
    }

    #endregion

}
