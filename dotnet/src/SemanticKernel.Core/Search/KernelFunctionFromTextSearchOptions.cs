// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Options that can be provided when creating a <see cref="KernelFunction"/> from a <see cref="ITextSearch{T}"/>.
/// </summary>
public sealed class KernelFunctionFromTextSearchOptions
{
    /// <summary>
    /// The name to use for the function. If null, it will default to one derived from the method represented by the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>.
    /// </summary>
    public string? FunctionName { get; init; }

    /// <summary>
    /// The description to use for the function. If null, it will default to one derived from the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>, if possible
    /// (e.g. via a <see cref="DescriptionAttribute"/> on the method).
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// Optional parameter descriptions. If null, it will default to one derived from the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>.
    /// </summary>
    public IEnumerable<KernelParameterMetadata>? Parameters { get; init; }

    /// <summary>
    /// Optional return parameter description. If null, it will default to one derived from the passed <see cref="Delegate"/> or <see cref="MethodInfo"/>.
    /// </summary>
    public KernelReturnParameterMetadata? ReturnParameter { get; init; }

    /// <summary>
    /// Optional <see cref="SearchOptions"/> that can be used to configure the search function.
    /// </summary>
    public SearchOptions? SearchOptions { get; init; }

    /// <summary>
    /// The delegate for this search function.
    /// </summary>
    public Delegate? Delegate { get; init; }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> instance.
    /// </summary>
    public KernelFunction CreateKernelFunction()
    {
        return KernelFunctionFactory.CreateFromMethod(
                this.Delegate!,
                this.ToKernelFunctionFromMethodOptions());
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <param name="mapToString"></param>
    /// <returns></returns>
    public static KernelFunctionFromTextSearchOptions DefaultSearch(ITextSearch<string> textSearch, BasicFilterOptions? basicFilter = null, MapSearchResultToString? mapToString = null)
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
    public static KernelFunctionFromTextSearchOptions DefaultGetSearchResults(ITextSearch<TextSearchResult> textSearch, BasicFilterOptions? basicFilter = null)
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

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <param name="mapToString"></param>
    /// <returns></returns>
    public static KernelFunctionFromTextSearchOptions DefaultSearch<T>(ITextSearch2<T> textSearch, BasicFilterOptions? basicFilter = null, MapSearchResultToString? mapToString = null) where T : class
    {
        async Task<IEnumerable<string>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                arguments.TryGetValue("query", out var query);
                query = query?.ToString() ?? string.Empty;

                var parameters = function.Metadata.Parameters;

                arguments.TryGetValue("count", out var count);
                arguments.TryGetValue("count", out var skip);
                SearchOptions searchOptions = new()
                {
                    Count = (count as int?) ?? GetDefaultValue(parameters, "count", 2),
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0),
                    BasicFilter = basicFilter
                };

                var result = await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
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
    public static KernelFunctionFromTextSearchOptions DefaultGetSearchResults<T>(ITextSearch2<T> textSearch, BasicFilterOptions? basicFilter = null) where T : class
    {
        async Task<IEnumerable<TextSearchResult>> GetSearchResultsAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                arguments.TryGetValue("query", out var query);
                query = query?.ToString() ?? string.Empty;

                var parameters = function.Metadata.Parameters;

                arguments.TryGetValue("count", out var count);
                arguments.TryGetValue("count", out var skip);
                SearchOptions searchOptions = new()
                {
                    Count = (count as int?) ?? GetDefaultValue(parameters, "count", 2),
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0),
                    BasicFilter = basicFilter
                };

                var result = await textSearch.GetTextSearchResultsAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
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

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <param name="mapToString"></param>
    /// <returns></returns>
    public static KernelFunctionFromTextSearchOptions DefaultSearch(ITextSearch3 textSearch, BasicFilterOptions? basicFilter = null, MapSearchResultToString? mapToString = null)
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
    public static KernelFunctionFromTextSearchOptions DefaultGetSearchResults(ITextSearch3 textSearch, BasicFilterOptions? basicFilter = null)
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

                var result = await textSearch.GetTextSearchResultsAsync(query?.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
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
    /// Create an instance of <see cref="KernelFunctionFromMethodOptions"/>
    /// </summary>
    private KernelFunctionFromMethodOptions ToKernelFunctionFromMethodOptions()
    {
        return new()
        {
            FunctionName = this.FunctionName,
            Description = this.Description,
            Parameters = this.Parameters,
            ReturnParameter = this.ReturnParameter,
        };
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
