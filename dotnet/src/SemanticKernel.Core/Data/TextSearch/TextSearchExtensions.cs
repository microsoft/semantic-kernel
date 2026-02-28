// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Provides extension methods for interacting with <see cref="ITextSearch"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class TextSearchExtensions
{
    #region KernelPlugin factory methods
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
    /// <returns>A <see cref="KernelPlugin"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateWithSearch which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelPlugin CreateWithSearch(this ITextSearch textSearch, string pluginName, string? description = null) =>
        textSearch.CreateWithSearch(TextSearchOptions.DefaultTop, pluginName, description);

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `Search` which
    /// will return a <see cref="IEnumerable{String}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreateWithSearch(this ITextSearch textSearch, int top, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateSearch(top)]);
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
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateWithSearch which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelPlugin CreateWithSearch(this ITextSearch textSearch, string pluginName, JsonSerializerOptions jsonSerializerOptions, string? description = null) =>
        textSearch.CreateWithSearch(TextSearchOptions.DefaultTop, pluginName, jsonSerializerOptions, description);

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `Search` which
    /// will return a <see cref="IEnumerable{String}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelPlugin CreateWithSearch(this ITextSearch textSearch, int top, string pluginName, JsonSerializerOptions jsonSerializerOptions, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateSearch(top, jsonSerializerOptions)]);
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
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetTextSearchResults operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateWithGetTextSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelPlugin CreateWithGetTextSearchResults(this ITextSearch textSearch, string pluginName, string? description = null) =>
        textSearch.CreateWithGetTextSearchResults(TextSearchOptions.DefaultTop, pluginName, description);

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetSearchResults` which
    /// will return a <see cref="IEnumerable{TextSearchResult}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetTextSearchResults operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreateWithGetTextSearchResults(this ITextSearch textSearch, int top, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetTextSearchResults(top)]);
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
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetTextSearchResults operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateWithGetTextSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelPlugin CreateWithGetTextSearchResults(this ITextSearch textSearch, string pluginName, JsonSerializerOptions jsonSerializerOptions, string? description = null) =>
        textSearch.CreateWithGetTextSearchResults(TextSearchOptions.DefaultTop, pluginName, jsonSerializerOptions, description);

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetSearchResults` which
    /// will return a <see cref="IEnumerable{TextSearchResult}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetTextSearchResults operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelPlugin CreateWithGetTextSearchResults(this ITextSearch textSearch, int top, string pluginName, JsonSerializerOptions jsonSerializerOptions, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetTextSearchResults(top, jsonSerializerOptions)]);
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
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetSearchResults operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateWithGetSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelPlugin CreateWithGetSearchResults(this ITextSearch textSearch, string pluginName, string? description = null) =>
        textSearch.CreateWithGetSearchResults(TextSearchOptions.DefaultTop, pluginName, description);

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetSearchResults` which
    /// will return a <see cref="IEnumerable{TextSearchResult}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetSearchResults operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreateWithGetSearchResults(this ITextSearch textSearch, int top, string pluginName, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetSearchResults(top)]);
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
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetSearchResults operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateWithGetSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelPlugin CreateWithGetSearchResults(this ITextSearch textSearch, string pluginName, JsonSerializerOptions jsonSerializerOptions, string? description = null) =>
        textSearch.CreateWithGetSearchResults(TextSearchOptions.DefaultTop, pluginName, jsonSerializerOptions, description);

    /// <summary>
    /// Creates a plugin from an ITextSearch implementation.
    /// </summary>
    /// <remarks>
    /// The plugin will have a single function called `GetSearchResults` which
    /// will return a <see cref="IEnumerable{TextSearchResult}"/>
    /// </remarks>
    /// <param name="textSearch">The instance of ITextSearch to be used by the plugin.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <returns>A <see cref="KernelPlugin"/> instance with a GetSearchResults operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelPlugin CreateWithGetSearchResults(this ITextSearch textSearch, int top, string pluginName, JsonSerializerOptions jsonSerializerOptions, string? description = null)
    {
        Verify.NotNull(textSearch);
        Verify.NotNull(pluginName);

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, [textSearch.CreateGetSearchResults(top, jsonSerializerOptions)]);
    }
    #endregion

    #region KernelFunction factory methods
    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateSearch with top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelFunction CreateSearch(this ITextSearch textSearch, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null) =>
        textSearch.CreateSearch(searchOptions?.Top ?? TextSearchOptions.DefaultTop, options, searchOptions);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="top">Maximum number of search results to return.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateSearch(this ITextSearch textSearch, int top, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<string>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken, int? count = null, int? skip = null)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Skip = skip ?? 0,
                Filter = CreateBasicFilter(options, arguments)
            };

            var results = textSearch.SearchAsync(query?.ToString()!, count ?? top, searchOptions, cancellationToken);
            return await results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultSearchMethodOptions(top);
        return KernelFunctionFactory.CreateFromMethod(
                SearchAsync,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateSearch with top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelFunction CreateSearch(this ITextSearch textSearch, JsonSerializerOptions jsonSerializerOptions, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null) =>
        textSearch.CreateSearch(searchOptions?.Top ?? TextSearchOptions.DefaultTop, jsonSerializerOptions, options, searchOptions);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelFunction CreateSearch(this ITextSearch textSearch, int top, JsonSerializerOptions jsonSerializerOptions, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<string>> SearchAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken, int? count = null, int? skip = null)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Skip = skip ?? 0,
                Filter = CreateBasicFilter(options, arguments)
            };

            var results = textSearch.SearchAsync(query?.ToString()!, count ?? top, searchOptions, cancellationToken);
            return await results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultSearchMethodOptions(top, jsonSerializerOptions);
        return KernelFunctionFactory.CreateFromMethod(
                SearchAsync,
                jsonSerializerOptions,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateGetTextSearchResults with top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelFunction CreateGetTextSearchResults(this ITextSearch textSearch, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null) =>
        textSearch.CreateGetTextSearchResults(searchOptions?.Top ?? TextSearchOptions.DefaultTop, options, searchOptions);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateGetTextSearchResults(this ITextSearch textSearch, int top, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<TextSearchResult>> GetTextSearchResultAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken, int? count = null, int? skip = null)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Skip = skip ?? 0,
                Filter = CreateBasicFilter(options, arguments)
            };

            var results = textSearch.GetTextSearchResultsAsync(query?.ToString()!, count ?? top, searchOptions, cancellationToken);
            return await results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultGetTextSearchResultsMethodOptions(top);
        return KernelFunctionFactory.CreateFromMethod(
                GetTextSearchResultAsync,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateGetTextSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelFunction CreateGetTextSearchResults(this ITextSearch textSearch, JsonSerializerOptions jsonSerializerOptions, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null) =>
            textSearch.CreateGetTextSearchResults(searchOptions?.Top ?? TextSearchOptions.DefaultTop, jsonSerializerOptions, options, searchOptions);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelFunction CreateGetTextSearchResults(this ITextSearch textSearch, int top, JsonSerializerOptions jsonSerializerOptions, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<TextSearchResult>> GetTextSearchResultAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken, int? count = null, int? skip = null)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Skip = skip ?? 0,
                Filter = CreateBasicFilter(options, arguments)
            };

            var results = textSearch.GetTextSearchResultsAsync(query?.ToString()!, count ?? top, searchOptions, cancellationToken);
            return await results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultGetTextSearchResultsMethodOptions(top, jsonSerializerOptions);
        return KernelFunctionFactory.CreateFromMethod(
                GetTextSearchResultAsync,
                jsonSerializerOptions,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateGetSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelFunction CreateGetSearchResults(this ITextSearch textSearch, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null) =>
            textSearch.CreateGetSearchResults(searchOptions?.Top ?? TextSearchOptions.DefaultTop, options, searchOptions);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelFunction CreateGetSearchResults(this ITextSearch textSearch, int top, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<object>> GetSearchResultAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken, int? count = null, int? skip = null)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Skip = skip ?? 0,
                Filter = CreateBasicFilter(options, arguments)
            };

            var results = textSearch.GetSearchResultsAsync(query?.ToString()!, count ?? top, searchOptions, cancellationToken);
            return await results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultGetSearchResultsMethodOptions(top);
        return KernelFunctionFactory.CreateFromMethod(
                GetSearchResultAsync,
                options);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    [Obsolete("This property is deprecated and will be removed in future versions. Use CreateGetSearchResults which takes the top parameter instead.", false)]
    [ExcludeFromCodeCoverage]
    public static KernelFunction CreateGetSearchResults(this ITextSearch textSearch, JsonSerializerOptions jsonSerializerOptions, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null) =>
        textSearch.CreateGetSearchResults(searchOptions?.Top ?? TextSearchOptions.DefaultTop, jsonSerializerOptions, options, searchOptions);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> which invokes <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    /// <param name="textSearch">The ITextSearch instance to use.</param>
    /// <param name="top">The maximum number of search results to return.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization and deserialization of various aspects of the function.</param>
    /// <param name="options">Optional KernelFunctionFromMethodOptions which allow the KernelFunction metadata to be specified.</param>
    /// <param name="searchOptions">Optional TextSearchOptions which override the options provided when the function is invoked.</param>
    /// <returns>A <see cref="KernelFunction"/> instance with a Search operation that calls the provided <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.</returns>
    public static KernelFunction CreateGetSearchResults(this ITextSearch textSearch, int top, JsonSerializerOptions jsonSerializerOptions, KernelFunctionFromMethodOptions? options = null, TextSearchOptions? searchOptions = null)
    {
        async Task<IEnumerable<object>> GetSearchResultAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken, int? count = null, int? skip = null)
        {
            arguments.TryGetValue("query", out var query);
            if (string.IsNullOrEmpty(query?.ToString()))
            {
                return [];
            }

            var parameters = function.Metadata.Parameters;

            searchOptions ??= new()
            {
                Skip = skip ?? 0,
                Filter = CreateBasicFilter(options, arguments)
            };

            var results = textSearch.GetSearchResultsAsync(query?.ToString()!, count ?? top, searchOptions, cancellationToken);
            return await results.ToListAsync(cancellationToken).ConfigureAwait(false);
        }

        options ??= DefaultGetSearchResultsMethodOptions(top, jsonSerializerOptions);
        return KernelFunctionFactory.CreateFromMethod(
                GetSearchResultAsync,
                jsonSerializerOptions,
                options);
    }
    #endregion

    #region private
    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    [RequiresUnreferencedCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    private static KernelFunctionFromMethodOptions DefaultSearchMethodOptions(int defaultCount) =>
        new()
        {
            FunctionName = "Search",
            Description = "Perform a search for content related to the specified query and return string results",
            Parameters = GetDefaultKernelParameterMetadata(defaultCount),
            ReturnParameter = new() { ParameterType = typeof(List<string>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.SearchAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions DefaultSearchMethodOptions(int defaultCount, JsonSerializerOptions jsonSerializerOptions) =>
        new()
        {
            FunctionName = "Search",
            Description = "Perform a search for content related to the specified query and return string results",
            Parameters = CreateDefaultKernelParameterMetadata(defaultCount, jsonSerializerOptions),
            ReturnParameter = new(jsonSerializerOptions) { ParameterType = typeof(List<string>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    [RequiresUnreferencedCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    private static KernelFunctionFromMethodOptions DefaultGetTextSearchResultsMethodOptions(int defaultCount) =>
        new()
        {
            FunctionName = "GetTextSearchResults",
            Description = "Perform a search for content related to the specified query. The search will return the name, value and link for the related content.",
            Parameters = GetDefaultKernelParameterMetadata(defaultCount),
            ReturnParameter = new() { ParameterType = typeof(List<TextSearchResult>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.GetTextSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions DefaultGetTextSearchResultsMethodOptions(int defaultCount, JsonSerializerOptions jsonSerializerOptions) =>
        new()
        {
            FunctionName = "GetTextSearchResults",
            Description = "Perform a search for content related to the specified query. The search will return the name, value and link for the related content.",
            Parameters = CreateDefaultKernelParameterMetadata(defaultCount, jsonSerializerOptions),
            ReturnParameter = new(jsonSerializerOptions) { ParameterType = typeof(List<TextSearchResult>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    [RequiresUnreferencedCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    private static KernelFunctionFromMethodOptions DefaultGetSearchResultsMethodOptions(int defaultCount) =>
        new()
        {
            FunctionName = "GetSearchResults",
            Description = "Perform a search for content related to the specified query.",
            Parameters = GetDefaultKernelParameterMetadata(defaultCount),
            ReturnParameter = new() { ParameterType = typeof(List<TextSearchResult>) },
        };

    /// <summary>
    /// Create the default <see cref="KernelFunctionFromMethodOptions"/> for <see cref="ITextSearch.GetSearchResultsAsync(string, TextSearchOptions?, CancellationToken)"/>.
    /// </summary>
    private static KernelFunctionFromMethodOptions DefaultGetSearchResultsMethodOptions(int defaultCount, JsonSerializerOptions jsonSerializerOptions) =>
        new()
        {
            FunctionName = "GetSearchResults",
            Description = "Perform a search for content related to the specified query.",
            Parameters = CreateDefaultKernelParameterMetadata(defaultCount, jsonSerializerOptions),
            ReturnParameter = new(jsonSerializerOptions) { ParameterType = typeof(List<TextSearchResult>) },
        };

    /// <summary>
    /// Create a <see cref="TextSearchFilter" /> for the search based on any additional parameters included in the <see cref="KernelFunctionFromMethodOptions"/>
    /// </summary>
    /// <param name="options">Kernel function method options.</param>
    /// <param name="arguments">Kernel arguments.</param>
    private static TextSearchFilter? CreateBasicFilter(KernelFunctionFromMethodOptions? options, KernelArguments arguments)
    {
        if (options?.Parameters is null)
        {
            return null;
        }

        TextSearchFilter? filter = null;
        foreach (var parameter in options.Parameters)
        {
            // treat non standard parameters as equality filter clauses
            if (!parameter.Name.Equals("query", System.StringComparison.Ordinal) &&
                !parameter.Name.Equals("count", System.StringComparison.Ordinal) &&
                !parameter.Name.Equals("skip", System.StringComparison.Ordinal))
            {
                if (arguments.TryGetValue(parameter.Name, out var value) && value is not null)
                {
                    filter ??= new TextSearchFilter();
                    filter.Equality(parameter.Name, value);
                }
            }
        }

        return filter;
    }

    private static IEnumerable<KernelParameterMetadata> CreateDefaultKernelParameterMetadata(int defaultCount, JsonSerializerOptions jsonSerializerOptions)
    {
        return [
            new KernelParameterMetadata("query", jsonSerializerOptions) { Description = "What to search for", ParameterType = typeof(string), IsRequired = true },
            new KernelParameterMetadata("count", jsonSerializerOptions) { Description = "Number of results", ParameterType = typeof(int), IsRequired = false, DefaultValue = defaultCount },
            new KernelParameterMetadata("skip", jsonSerializerOptions) { Description = "Number of results to skip", ParameterType = typeof(int), IsRequired = false, DefaultValue = 0 },
        ];
    }

    [RequiresUnreferencedCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection for generating JSON schema for method parameters and return type, making it incompatible with AOT scenarios.")]
    private static IEnumerable<KernelParameterMetadata> GetDefaultKernelParameterMetadata(int defaultCount)
    {
        return s_kernelParameterMetadata ??= [
            new KernelParameterMetadata("query") { Description = "What to search for", ParameterType = typeof(string), IsRequired = true },
            new KernelParameterMetadata("count") { Description = "Number of results", ParameterType = typeof(int), IsRequired = false, DefaultValue = defaultCount },
            new KernelParameterMetadata("skip") { Description = "Number of results to skip", ParameterType = typeof(int), IsRequired = false, DefaultValue = 0 },
        ];
    }

    private static IEnumerable<KernelParameterMetadata>? s_kernelParameterMetadata;

    #endregion
}
