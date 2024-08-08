// Copyright (c) Microsoft. All rights reserved.

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

    /// <summary>
    /// TODO
    /// </summary>
    private static KernelPluginFromTextSearchOptions<T> CreateDefaultOptions<T>(ITextSearch<T> textSearch) where T : class
    {
        return new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultSearch(textSearch),
                KernelFunctionFromTextSearchOptions.DefaultGetSearchResults(textSearch),
            ]
        };
    }

    #endregion
}
