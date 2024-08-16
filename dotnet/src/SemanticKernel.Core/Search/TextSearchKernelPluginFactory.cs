// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Search;
/// <summary>
/// Provides static factory methods for creating Text Search KernelPlugin implementations.
/// </summary>
public static class TextSearchKernelPluginFactory
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
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearch(ITextSearch<string> textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultSearch(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
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
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearchResults(ITextSearch<TextSearchResult> textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultGetSearchResults(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }

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
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearch<T>(ITextSearch2<T> textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default) where T : class
    {
        options ??= new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultSearch(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
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
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearchResults<T>(ITextSearch2<T> textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default) where T : class
    {
        options ??= new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultGetSearchResults(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }

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
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearch(ITextSearch3 textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultSearch(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
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
    /// <param name="options">Optional plugin creation options.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateFromTextSearchResults(ITextSearch3 textSearch, string pluginName, string? description = null, KernelPluginFromTextSearchOptions? options = default)
    {
        options ??= new()
        {
            Functions =
            [
                KernelFunctionFromTextSearchOptions.DefaultGetSearchResults(textSearch),
            ]
        };

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, options.CreateKernelFunctions());
    }
}
