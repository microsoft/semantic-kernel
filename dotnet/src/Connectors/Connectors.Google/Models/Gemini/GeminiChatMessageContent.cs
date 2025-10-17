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

        this.CalledToolResults = [calledToolResult];
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class with multiple tool results.
    /// </summary>
    /// <param name="calledToolResults">The results of tools called by the kernel.</param>
    public GeminiChatMessageContent(IEnumerable<GeminiFunctionToolResult> calledToolResults)
        : base(
            role: AuthorRole.Tool,
            content: null,
            modelId: null,
            innerContent: null,
            encoding: Encoding.UTF8,
            metadata: null)
    {
        Verify.NotNull(calledToolResults);

        this.CalledToolResults = calledToolResults.ToList().AsReadOnly();
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
        this.CalledToolResults = calledToolResult != null ? [calledToolResult] : null;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiChatMessageContent"/> class with multiple tool results.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="calledToolResults">The results of tools called by the kernel.</param>
    /// <param name="metadata">Additional metadata</param>
    internal GeminiChatMessageContent(
        AuthorRole role,
        string? content,
        string modelId,
        IEnumerable<GeminiFunctionToolResult>? calledToolResults = null,
        GeminiMetadata? metadata = null)
        : base(
            role: role,
            content: content,
            modelId: modelId,
            innerContent: content,
            encoding: Encoding.UTF8,
            metadata: metadata)
    {
        this.CalledToolResults = calledToolResults?.ToList().AsReadOnly();
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
    /// The results of tools called by the kernel.
    /// </summary>
    public IReadOnlyList<GeminiFunctionToolResult>? CalledToolResults { get; }

    /// <summary>
    /// The result of tool called by the kernel (for backward compatibility).
    /// Returns the first tool result if multiple exist, or null if none.
    /// </summary>
    public GeminiFunctionToolResult? CalledToolResult => CalledToolResults?.FirstOrDefault();

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public new GeminiMetadata? Metadata => (GeminiMetadata?)base.Metadata;
}
