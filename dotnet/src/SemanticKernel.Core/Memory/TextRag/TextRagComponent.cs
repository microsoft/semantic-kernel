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
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A component that does a search based on any messages that the AI model is invoked with and injects the results into the AI model invocation context.
/// </summary>
[Experimental("SKEXP0130")]
public class TextRagComponent : ConversationStatePart
{
    private const string DefaultPluginSearchFunctionName = "Search";
    private const string DefaultPluginSearchFunctionDescription = "Allows searching for additional information to help answer the user question.";
    private const string DefaultContextPrompt = "Consider the following source information when responding to the user:";
    private const string DefaultIncludeCitationsPrompt = "Include citations to the relevant information where it is referenced in the response.";

    private readonly ITextSearch _textSearch;

    private readonly AIFunction[] _aIFunctions;

    /// <summary>
    /// Initializes a new instance of the <see cref="TextRagComponent"/> class.
    /// </summary>
    /// <param name="textSearch">The text search component to retrieve results from.</param>
    /// <param name="options">Options that configure the behavior of the component.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public TextRagComponent(ITextSearch textSearch, TextRagComponentOptions? options = default)
    {
        Verify.NotNull(textSearch);

        this._textSearch = textSearch;
        this.Options = options ?? new();

        this._aIFunctions =
        [
            AIFunctionFactory.Create(
            this.SearchAsync,
            name: this.Options.PluginSearchFunctionName ?? DefaultPluginSearchFunctionName,
            description: this.Options.PluginSearchFunctionDescription ?? DefaultPluginSearchFunctionDescription)
        ];
    }

    /// <summary>
    /// Gets the options that have been configured for this component.
    /// </summary>
    public TextRagComponentOptions Options { get; }

    /// <inheritdoc/>
    public override IReadOnlyCollection<AIFunction> AIFunctions
    {
        get
        {
            if (this.Options.SearchTime != TextRagComponentOptions.TextRagSearchTime.ViaPlugin)
            {
                return Array.Empty<AIFunction>();
            }

            return this._aIFunctions;
        }
    }

    /// <inheritdoc/>
    public override async Task<string> OnModelInvokeAsync(ICollection<ChatMessage> newMessages, CancellationToken cancellationToken = default)
    {
        if (this.Options.SearchTime != TextRagComponentOptions.TextRagSearchTime.BeforeAIInvoke)
        {
            return string.Empty;
        }

        Verify.NotNull(newMessages);

        string input = string.Join("\n", newMessages.Where(m => m is not null).Select(m => m.Text));

        var searchResults = await this._textSearch.GetTextSearchResultsAsync(
            input,
            new() { Top = this.Options.Top },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        // Format the results showing the content with source link and name for each result.
        var sb = new StringBuilder();
        sb.AppendLine(this.Options.ContextPrompt ?? DefaultContextPrompt);
        await foreach (var result in searchResults.Results.ConfigureAwait(false))
        {
            sb.AppendLine($"    Source Document Name: {result.Name}");
            sb.AppendLine($"    Source Document Link: {result.Link}");
            sb.AppendLine($"    Source Document Contents: {result.Value}");
            sb.AppendLine("    -----------------");
        }

        sb.AppendLine(this.Options.InclueCitationsPrompt ?? DefaultIncludeCitationsPrompt);
        sb.AppendLine("-------------------");

        return sb.ToString();
    }

    /// <summary>
    /// Plugin method to search the database on demand.
    /// </summary>
    [KernelFunction]
    public async Task<string> SearchAsync(string userQuestion, CancellationToken cancellationToken = default)
    {
        var searchResults = await this._textSearch.GetTextSearchResultsAsync(
            userQuestion,
            new() { Top = this.Options.Top },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        var results = await searchResults.Results.ToListAsync(cancellationToken).ConfigureAwait(false);

        return JsonSerializer.Serialize(results, TextRagSourceGenerationContext.Default.ListTextSearchResult);
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
