// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A component that does a search based on any messages that the AI model is invoked with and injects the results into the AI model invocation context.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class TextSearchProvider : AIContextProvider
{
    private const string DefaultPluginSearchFunctionName = "Search";
    private const string DefaultPluginSearchFunctionDescription = "Allows searching for additional information to help answer the user question.";
    private const string DefaultContextPrompt = "## Additional Context\nConsider the following information from source documents when responding to the user:";
    private const string DefaultIncludeCitationsPrompt = "Include citations to the source document with document name and link if document name and link is available.";

    private readonly ITextSearch _textSearch;
    private readonly ILogger<TextSearchProvider>? _logger;
    private readonly AIFunction[] _aIFunctions;

    /// <summary>
    /// Initializes a new instance of the <see cref="TextSearchProvider"/> class.
    /// </summary>
    /// <param name="textSearch">The text search component to retrieve results from.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="options">Options that configure the behavior of the component.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public TextSearchProvider(ITextSearch textSearch, ILoggerFactory? loggerFactory = default, TextSearchProviderOptions? options = default)
    {
        Verify.NotNull(textSearch);

        this._textSearch = textSearch;
        this._logger = loggerFactory?.CreateLogger<TextSearchProvider>();
        this.Options = options ?? new();

        this._aIFunctions =
        [
            AIFunctionFactory.Create(
            this.SearchAsync,
            name: this.Options.PluginFunctionName ?? DefaultPluginSearchFunctionName,
            description: this.Options.PluginFunctionDescription ?? DefaultPluginSearchFunctionDescription)
        ];
    }

    /// <summary>
    /// Gets the options that have been configured for this component.
    /// </summary>
    public TextSearchProviderOptions Options { get; }

    /// <inheritdoc/>
    public override async Task<AIContext> ModelInvokingAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        if (this.Options.SearchTime != TextSearchProviderOptions.RagBehavior.BeforeAIInvoke)
        {
            return new()
            {
                AIFunctions = this._aIFunctions.ToArray(),
            };
        }

        Verify.NotNull(newMessages);

        string input = string.Join("\n", newMessages.Where(m => m is not null).Select(m => m.Text));

        var searchResults = await this._textSearch.GetTextSearchResultsAsync(
            input,
            new() { Top = this.Options.Top },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        var results = await searchResults.Results.ToListAsync(cancellationToken).ConfigureAwait(false);

        var formatted = this.FormatResults(results);

        this._logger?.LogInformation("TextSearchBehavior: Retrieved {Count} search results.", results.Count);
        this._logger?.LogTrace("TextSearchBehavior:\nInput Messages:{Input}\nOutput context instructions:\n{Instructions}", input, formatted);

        return new() { Instructions = formatted };
    }

    /// <summary>
    /// Plugin method to search the database on demand.
    /// </summary>
    [KernelFunction]
    internal async Task<string> SearchAsync(string userQuestion, CancellationToken cancellationToken = default)
    {
        var searchResults = await this._textSearch.GetTextSearchResultsAsync(
            userQuestion,
            new() { Top = this.Options.Top },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        var results = await searchResults.Results.ToListAsync(cancellationToken).ConfigureAwait(false);

        var formatted = this.FormatResults(results);

        return formatted;
    }

    /// <summary>
    /// Format the results showing the content with source link and name for each result.
    /// </summary>
    /// <param name="results">The results to format.</param>
    /// <returns>The formatted results.</returns>
    private string FormatResults(List<TextSearchResult> results)
    {
        if (this.Options.ContextFormatter is not null)
        {
            return this.Options.ContextFormatter(results);
        }

        if (results.Count == 0)
        {
            return string.Empty;
        }

        var sb = new StringBuilder();
        sb.AppendLine(this.Options.ContextPrompt ?? DefaultContextPrompt);
        for (int i = 0; i < results.Count; i++)
        {
            var result = results[i];

            // Only output the doc name and link lines
            // if they are not empty to save tokens.
            if (!string.IsNullOrWhiteSpace(result.Name))
            {
                sb.AppendLine($"SourceDocName: {result.Name}");
            }
            if (!string.IsNullOrWhiteSpace(result.Link))
            {
                sb.AppendLine($"SourceDocLink: {result.Link}");
            }
            sb.AppendLine($"Contents: {result.Value}");
            sb.AppendLine("----");
        }
        sb.AppendLine(this.Options.IncludeCitationsPrompt ?? DefaultIncludeCitationsPrompt);
        sb.AppendLine();
        return sb.ToString();
    }
}

[JsonSourceGenerationOptions(JsonSerializerDefaults.General,
    UseStringEnumConverter = false,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    WriteIndented = false)]
[JsonSerializable(typeof(List<TextSearchResult>))]
internal partial class TextRagSourceGenerationContext : JsonSerializerContext
{
}
