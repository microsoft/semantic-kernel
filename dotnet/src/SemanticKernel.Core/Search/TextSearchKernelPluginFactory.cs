// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel;
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
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearch<T>(ITextSearch<T> textSearch, string pluginName, string? description = null, KernelFunctionFromMethodOptions? options = null) where T : class
    {
        async Task<KernelSearchResults<T>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
            {
                arguments.TryGetValue("query", out var query);
                query = query?.ToString() ?? string.Empty;

                arguments.TryGetValue("count", out var count);
                arguments.TryGetValue("count", out var skip);
                SearchOptions searchOptions = new()
                {
                    Count = (count as int?) ?? 2,
                    Offset = (skip as int?) ?? 0
                };

                return await textSearch.SearchAsync(query.ToString()!, searchOptions, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                throw;
            }
        }

        var function = KernelFunctionFactory.CreateFromMethod(
                SearchAsync,
                options ?? CreateDefaultMethodOptions(textSearch));

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [function]);
    }

    #region private

    private static KernelFunctionFromMethodOptions CreateDefaultMethodOptions<T>(ITextSearch<T> textSearch) where T : class
    {
        var functionName = nameof(ITextSearch<T>.SearchAsync);
        return new()
        {
            FunctionName = functionName,
            Description = "Perform a search for content related to the specified query",
            Parameters =
            [
                new KernelParameterMetadata("query") { Description = "What to search for", IsRequired = true },
                new KernelParameterMetadata("count") { Description = "Number of results", IsRequired = false, DefaultValue = 2 },
                new KernelParameterMetadata("skip") { Description = "Number of results skip", IsRequired = false, DefaultValue = 0 },
            ],
        };
    }

    #endregion
}
