// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google.Core;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Gemini specialized chat message content
/// </summary>
public sealed class GeminiChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Creates a new instance of the <see cref="GeminiChatMessageContent"/> class
    /// </summary>
    [JsonConstructor]
    public GeminiChatMessageContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class.
    /// </summary>
    /// <param name="calledToolResult">The result of tool called by the kernel.</param>
    public GeminiChatMessageContent(GeminiFunctionToolResult calledToolResult)
        : base(
            role: AuthorRole.Tool,
            content: null,
            modelId: null,
            innerContent: null,
            encoding: Encoding.UTF8,
            metadata: null)
    {
        Verify.NotNull(calledToolResult);

        this.CalledToolResult = calledToolResult;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="calledToolResult">The result of tool called by the kernel.</param>
    /// <param name="metadata">Additional metadata</param>
    internal GeminiChatMessageContent(
        AuthorRole role,
        string? content,
        string modelId,
        GeminiFunctionToolResult? calledToolResult = null,
        GeminiMetadata? metadata = null)
        : base(
            role: role,
            content: content,
            modelId: modelId,
            innerContent: content,
            encoding: Encoding.UTF8,
            metadata: metadata)
    {
        this.CalledToolResult = calledToolResult;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="functionsToolCalls">Tool calls parts returned by model</param>
    /// <param name="metadata">Additional metadata</param>
    internal GeminiChatMessageContent(
        AuthorRole role,
        string? content,
        string modelId,
        IEnumerable<GeminiPart.FunctionCallPart>? functionsToolCalls,
        GeminiMetadata? metadata = null)
        : base(
            role: role,
            content: content,
            modelId: modelId,
            innerContent: content,
            encoding: Encoding.UTF8,
            metadata: metadata)
    {
        this.ToolCalls = functionsToolCalls?.Select(tool => new GeminiFunctionToolCall(tool)).ToList();
    }

    /// <summary>
    /// A list of the tools returned by the model with arguments.
    /// </summary>
    public IReadOnlyList<GeminiFunctionToolCall>? ToolCalls { get; }

    /// <summary>
    /// The result of tool called by the kernel.
    /// </summary>
    public GeminiFunctionToolResult? CalledToolResult { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public new GeminiMetadata? Metadata => (GeminiMetadata?)base.Metadata;
}
