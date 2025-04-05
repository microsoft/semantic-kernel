// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Plugins.Web.Brave;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Microsoft.SemanticKernel.Plugins.Web.Tavily;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register <see cref="ITextSearch"/> for use with <see cref="IKernelBuilder"/>.
/// </summary>
public static class WebKernelBuilderExtensions
{
    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="BingTextSearchOptions"/> to used when creating the <see cref="BingTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddBingTextSearch(
        this IKernelBuilder builder,
        string apiKey,
        BingTextSearchOptions? options = null,
        string? serviceId = default)
    {
        Verify.NotNull(builder);
        builder.Services.AddBingTextSearch(apiKey, options, serviceId);
        return builder;
    }

    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="BraveTextSearchOptions"/> to used when creating the <see cref="BraveTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddBraveTextSearch(
        this IKernelBuilder builder,
        string apiKey,
        BraveTextSearchOptions? options = null,
        string? serviceId = default)
    {
        builder.Services.AddBraveTextSearch(apiKey, options, serviceId);

        return builder;
    }

    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="GoogleTextSearchOptions"/> to used when creating the <see cref="GoogleTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddGoogleTextSearch(
        this IKernelBuilder builder,
        string searchEngineId,
        string apiKey,
        GoogleTextSearchOptions? options = null,
        string? serviceId = default)
    {
        Verify.NotNull(builder);
        builder.Services.AddGoogleTextSearch(searchEngineId, apiKey, options, serviceId);

        return builder;
    }

    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="TavilyTextSearchOptions"/> to used when creating the <see cref="TavilyTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IKernelBuilder AddTavilyTextSearch(
        this IKernelBuilder builder,
        string apiKey,
        TavilyTextSearchOptions? options = null,
        string? serviceId = default)
    {
        Verify.NotNull(builder);
        builder.Services.AddTavilyTextSearch(apiKey, options, serviceId);
        return builder;
    }
}
