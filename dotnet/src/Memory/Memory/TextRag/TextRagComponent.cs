// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A component that does a search based on any messages that the AI is invoked with and injects the results into the AI invocation context.
/// </summary>
public class TextRagComponent : ConversationStateExtension
{
    private readonly ITextSearch _textSearch;

    /// <summary>
    /// Initializes a new instance of the <see cref="TextRagComponent"/> class.
    /// </summary>
    /// <param name="textSearch">The text search component to retrieve results from.</param>
    /// <param name="options"></param>
    /// <exception cref="ArgumentNullException"></exception>
    public TextRagComponent(ITextSearch textSearch, TextRagComponentOptions options)
    {
        Verify.NotNull(textSearch);

        this._textSearch = textSearch;
        this.Options = options ?? throw new ArgumentNullException(nameof(options));
    }

    /// <summary>
    /// Gets the options that have been configured for this component.
    /// </summary>
    public TextRagComponentOptions Options { get; }

    /// <inheritdoc/>
    public override async Task<string> OnAIInvocationAsync(ICollection<ChatMessageContent> newMessages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(newMessages);

        string input = string.Join("\n", newMessages.Where(m => m is not null).Select(m => m.Content));

        var searchResults = await this._textSearch.GetTextSearchResultsAsync(
            input,
            new() { Top = this.Options.Top },
            cancellationToken: cancellationToken).ConfigureAwait(false);

        // Format the results showing the content with source link and name for each result.
        var sb = new StringBuilder();
        sb.AppendLine("Please consider the following source information when responding to the user:");
        await foreach (var result in searchResults.Results.ConfigureAwait(false))
        {
            sb.AppendLine($"    Source Document Name: {result.Name}");
            sb.AppendLine($"    Source Document Link: {result.Link}");
            sb.AppendLine($"    Source Document Contents: {result.Value}");
            sb.AppendLine("    -----------------");
        }

        sb.AppendLine("Include citations to the relevant information where it is referenced in the response.");
        sb.AppendLine("-------------------");

        return sb.ToString();
    }
}
