// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Plugins.Web.Bing;
using Microsoft.SemanticKernel.Plugins.Web.Brave;
using Microsoft.SemanticKernel.Plugins.Web.Google;
using Microsoft.SemanticKernel.Plugins.Web.Tavily;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register <see cref="ITextSearch"/> for use with <see cref="IServiceCollection"/>.
/// </summary>
public static class WebServiceCollectionExtensions
{
    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="BingTextSearchOptions"/> to used when creating the <see cref="BingTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddBingTextSearch(
        this IServiceCollection services,
        string apiKey,
        BingTextSearchOptions? options = null,
        string? serviceId = default)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextSearch>(
            serviceId,
            (sp, obj) =>
            {
                var selectedOptions = options ?? sp.GetService<BingTextSearchOptions>();

                return new BingTextSearch(apiKey, selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="BingTextSearchOptions"/> to used when creating the <see cref="BingTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddBraveTextSearch(
        this IServiceCollection services,
        string apiKey,
        BraveTextSearchOptions? options = null,
        string? serviceId = default)
    {
        services.AddKeyedSingleton<ITextSearch>(
            serviceId,
            (sp, obj) =>
            {
                var selectedOptions = options ?? sp.GetService<BraveTextSearchOptions>();

                return new BraveTextSearch(apiKey, selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="searchEngineId">Google Search Engine ID (looks like "a12b345...")</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="GoogleTextSearchOptions"/> to used when creating the <see cref="GoogleTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddGoogleTextSearch(
        this IServiceCollection services,
        string searchEngineId,
        string apiKey,
        GoogleTextSearchOptions? options = null,
        string? serviceId = default)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextSearch>(
            serviceId,
            (sp, obj) =>
            {
                var selectedOptions = options ?? sp.GetService<GoogleTextSearchOptions>();

                return new GoogleTextSearch(searchEngineId, apiKey, selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register an <see cref="ITextSearch"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="apiKey">The API key credential used to authenticate requests against the Search service.</param>
    /// <param name="options">Instance of <see cref="TavilyTextSearchOptions"/> to used when creating the <see cref="TavilyTextSearch"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    public static IServiceCollection AddTavilyTextSearch(
        this IServiceCollection services,
        string apiKey,
        TavilyTextSearchOptions? options = null,
        string? serviceId = default)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextSearch>(
            serviceId,
            (sp, _) =>
            {
                var selectedOptions = options ?? sp.GetService<TavilyTextSearchOptions>();

                return new TavilyTextSearch(apiKey, selectedOptions);
            });

        return services;
    }
}
