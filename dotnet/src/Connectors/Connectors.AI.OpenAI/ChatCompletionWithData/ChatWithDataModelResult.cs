// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

/// <summary>
/// Represents result of a chat completion with data.
/// </summary>
public class ChatWithDataModelResult
{
    /// <summary>
    /// A unique identifier associated with chat completion with data response.
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// The first timestamp associated with generation activity for chat completion with data response,
    /// represented as seconds since the beginning of the Unix epoch of 00:00 on 1 Jan 1970.
    /// </summary>
    public DateTimeOffset Created { get; }

    /// <summary>
    /// Contains tool content, which stores citations from data source.
    /// For more information see <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/use-your-data#conversation-history-for-better-results"/>.
    /// </summary>
    public string? ToolContent { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatWithDataModelResult"/> class.
    /// </summary>
    /// <param name="id">A unique identifier associated with chat completion with data response.</param>
    /// <param name="created">The first timestamp associated with generation activity for chat completion with data response.</param>
    public ChatWithDataModelResult(string id, DateTimeOffset created)
    {
        this.Id = id;
        this.Created = created;
    }
}
