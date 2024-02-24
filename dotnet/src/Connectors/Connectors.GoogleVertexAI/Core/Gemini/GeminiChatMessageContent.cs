// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Gemini specialized chat message content
/// </summary>
public sealed class GeminiChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal GeminiChatMessageContent(
        AuthorRole role,
        string? content,
        string modelId,
        GeminiMetadata? metadata = null)
        : base(
            role: role,
            content: content,
            modelId: modelId,
            innerContent: content,
            encoding: Encoding.UTF8,
            metadata: metadata) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="toolCalls">Tool calls parts returned by model</param>
    /// <param name="metadata">Additional metadata</param>
    internal GeminiChatMessageContent(
        AuthorRole role,
        string? content,
        string modelId,
        IReadOnlyList<GeminiPart.FunctionCallPart> toolCalls,
        GeminiMetadata? metadata = null)
        : base(
            role: role,
            content: content,
            modelId: modelId,
            innerContent: content,
            encoding: Encoding.UTF8,
            metadata: metadata)
    {
        this.ToolCalls = toolCalls;
    }

    /// <summary>
    /// A list of the tools called by the model.
    /// </summary>
    public IReadOnlyList<GeminiPart.FunctionCallPart>? ToolCalls { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public new GeminiMetadata? Metadata => (GeminiMetadata?)base.Metadata;

    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <returns>The <see cref="GeminiFunctionToolCall"/> or empty collection if no function was returned by the model.</returns>
    public IReadOnlyList<GeminiFunctionToolCall> GetGeminiFunctionToolCalls()
        => this.ToolCalls?.Select(functionCallPart => new GeminiFunctionToolCall(functionCallPart)).ToList() ?? new List<GeminiFunctionToolCall>();
}
