// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugins.web;

import com.microsoft.semantickernel.connectors.WebSearchEngineConnector;
import com.microsoft.semantickernel.connectors.WebSearchEngineConnector.WebPage;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import java.util.stream.Collectors;
import reactor.core.publisher.Mono;

/// <summary>
/// Web search engine plugin (e.g. Bing).
/// </summary>
public class WebSearchEnginePlugin {

    /// <summary>
    /// The count parameter name.
    /// </summary>
    public static final String COUNT_PARAM = "count";

    /// <summary>
    /// The offset parameter name.
    /// </summary>
    public static final String OFFSET_PARAM = "offset";

    private final WebSearchEngineConnector connector;

    /// <summary>
    /// Initializes a new instance of the <see cref="WebSearchEnginePlugin"/> class.
    /// </summary>
    /// <param name="connector">The web search engine connector.</param>
    public WebSearchEnginePlugin(WebSearchEngineConnector connector) {
        this.connector = connector;
    }

    /// <summary>
    /// Performs a web search using the provided query, count, and offset.
    /// </summary>
    /// <param name="query">The text to search for.</param>
    /// <param name="count">The number of results to return. Default is 1.</param>
    /// <param name="offset">The number of results to skip. Default is 0.</param>
    /// <param name="cancellationToken">A cancellation token to observe while waiting for the task to complete.</param>
    /// <returns>A task that represents the asynchronous operation. The value of the TResult parameter contains the search results as a string.</returns>
    /// <remarks>
    /// This method is marked as "unsafe." The usage of JavaScriptEncoder.UnsafeRelaxedJsonEscaping may introduce security risks.
    /// Only use this method if you are aware of the potential risks and have validated the input to prevent security vulnerabilities.
    /// </remarks>
    @DefineKernelFunction(name = "search", description = "Searches the web for the given query")
    public Mono<String> searchAsync(
        @KernelFunctionParameter(description = "The search query", name = "query", type = String.class) String query,
        @KernelFunctionParameter(description = "The number of results to return", name = "count", defaultValue = "1", type = int.class) int count,
        @KernelFunctionParameter(description = "The number of results to skip", name = "offset", defaultValue = "0", type = int.class) int offset) {

        return connector.searchAsync(query, count, offset).map(results -> {

            if (results == null || results.isEmpty()) {
                throw new SKException("Failed to get a response from the web search engine.");
            }

            return count == 1
                ? results.get(0).getSnippet()
                // TODO: .NET code does `JsonSerializer.Serialize(results, s_jsonOptionsCache)` here
                // The joiner results in "[\"result1\",\"result2\"]"
                : results.stream()
                    .limit(count)
                    .map(WebPage::getSnippet)
                    .collect(Collectors.joining("\",\"", "[\"", "\"]"));
        });
    }
}
