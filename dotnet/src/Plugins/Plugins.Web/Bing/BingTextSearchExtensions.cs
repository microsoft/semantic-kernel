// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Provides extension methods for interacting with <see cref="BingTextSearch"/> and related types.
/// </summary>
public static class BingTextSearchExtensions
{
    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetBingWebPages` which
    /// will return a <see cref="IEnumerable{BingWebPage}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A KernelPlugin instance whose functions correspond to the OpenAPI operations.</returns>
    public static KernelPlugin CreateKernelPluginWithGetBingWebPages(this BingTextSearch textSearch, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetBingWebPages()]);
    }

    /// <summary>
    /// TODO
    /// </summary>
    /// <param name="textSearch"></param>
    /// <param name="basicFilter"></param>
    /// <returns></returns>
    public static KernelFunction CreateGetBingWebPages(this BingTextSearch textSearch, BasicFilterOptions? basicFilter = null)
    {
        return BingTextSearchKernelPluginFactory.GetBingWebPages(textSearch, basicFilter).CreateKernelFunction();
    }
}
