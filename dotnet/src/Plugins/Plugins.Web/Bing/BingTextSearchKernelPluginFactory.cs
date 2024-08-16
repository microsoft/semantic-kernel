// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides static factory methods for creating Bing Text Search KernelPlugin implementations.
/// </summary>
public static class BingTextSearchKernelPluginFactory
{
    /// <summary>
    /// Creates a plugin from an BingTextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetBingWebPages` which
    /// will return a <see cref="IEnumerable{BingWebPage}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromBingWebPages(BingTextSearch textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                GetBingWebPages(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <returns></returns>
    public static KernelFunctionFromTextSearchOptions GetBingWebPages(BingTextSearch textSearch, BasicFilterOptions? basicFilter = null)
    {
        async Task<IEnumerable<BingWebPage>> GetBingWebPagesAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
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

                var result = await ((ITextSearch<BingWebPage>)textSearch).SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        return new()
        {
            Delegate = GetBingWebPagesAsync,
            FunctionName = "GetBingWebPages",
            Description = "Perform a search for content related to the specified query. The search will return an object representing a Bing web page.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };
    }

    /// <summary>
    /// Creates a plugin from an BingTextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetBingWebPages` which
    /// will return a <see cref="IEnumerable{BingWebPage}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromBingWebPages(BingTextSearch2 textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                GetBingWebPages(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <returns></returns>
    public static KernelFunctionFromTextSearchOptions GetBingWebPages(BingTextSearch2 textSearch, BasicFilterOptions? basicFilter = null)
    {
        async Task<IEnumerable<BingWebPage>> GetBingWebPagesAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
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

                var result = await textSearch.GetSearchResultsAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        return new()
        {
            Delegate = GetBingWebPagesAsync,
            FunctionName = "GetBingWebPages",
            Description = "Perform a search for content related to the specified query. The search will return an object representing a Bing web page.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };
    }

    /// <summary>
    /// Creates a plugin from an BingTextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetBingWebPages` which
    /// will return a <see cref="IEnumerable{BingWebPage}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromBingWebPages(BingTextSearch3 textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                GetBingWebPages(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <returns></returns>
    public static KernelFunctionFromTextSearchOptions GetBingWebPages(BingTextSearch3 textSearch, BasicFilterOptions? basicFilter = null)
    {
        async Task<IEnumerable<BingWebPage>> GetBingWebPagesAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
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

                var result = await textSearch.GetSearchResultsAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
                return await result.Results.ToListAsync(cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        return new()
        {
            Delegate = GetBingWebPagesAsync,
            FunctionName = "GetBingWebPages",
            Description = "Perform a search for content related to the specified query. The search will return an object representing a Bing web page.",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
            ReturnParameter = new() { ParameterType = typeof(KernelSearchResults<TextSearchResult>) },
        };
    }

    #region private

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
