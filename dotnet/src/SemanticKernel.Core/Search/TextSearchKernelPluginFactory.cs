// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Search;
/// <summary>
/// Provides static factory methods for creating Text Search KernelPlugin implementations.
/// </summary>
public static class TextSearchKernelPluginFactory
{
    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearch<T>(ITextSearch<T> textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions<T>? options = default) where T : class
    {
        options ??= CreateDefaultOptions(textSearch);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }

    #region private

    private static int GetDefaultValue(IReadOnlyList<KernelParameterMetadata> parameters, string name, int defaultValue)
    {
        var value = parameters.FirstOrDefault(parameter => parameter.Name == name)?.DefaultValue;
        return value is int intValue ? intValue : defaultValue;
    }

    private static KernelPluginFromTextSearchOptions<T> CreateDefaultOptions<T>(ITextSearch<T> textSearch) where T : class
    {
        List<KernelFunctionFromTextSearchOptions> functions = [];
        KernelPluginFromTextSearchOptions<T> options = new()
        {
            Functions = functions
        };

        async Task<string> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
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
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0)
                };

                var result = await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                var resultList = await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
                return options.MapToString!(resultList);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        async Task<IEnumerable<T>> GetSearchResultsAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
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
                    Offset = (skip as int?) ?? GetDefaultValue(parameters, "skip", 0)
                };

                var result = await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        KernelFunctionFromTextSearchOptions search = new()
        {
            Delegate = SearchAsync,
            FunctionName = "Search",
            Description = "Perform a search for content related to the specified query and return string results",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<string>) },
        };
        functions.Add(search);

        KernelFunctionFromTextSearchOptions getSearchResults = new()
        {
            Delegate = GetSearchResultsAsync,
            FunctionName = "Search",
            Description = "Perform a search for content related to the specified query",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<T>) },
        };
        functions.Add(getSearchResults);

        return options;
    }

    #endregion
}
