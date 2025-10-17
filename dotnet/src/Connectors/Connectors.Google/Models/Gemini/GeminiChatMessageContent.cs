﻿// Copyright (c) Microsoft. All rights reserved.

using System;
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

        // Parse plugin and function names from FullyQualifiedName
        var (pluginName, functionName) = ParseFullyQualifiedName(calledToolResult.FullyQualifiedName);

        // Also populate Items collection with FunctionResultContent for compatibility with FunctionChoiceBehavior
        this.Items.Add(new FunctionResultContent(
            functionName: functionName,
            pluginName: pluginName,
            callId: null, // Gemini doesn't provide call IDs
            result: calledToolResult.FunctionResult));
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

        // Also populate Items collection with FunctionResultContent for compatibility with FunctionChoiceBehavior
        if (calledToolResult is not null)
        {
            // Parse plugin and function names from FullyQualifiedName
            var (pluginName, functionName) = ParseFullyQualifiedName(calledToolResult.FullyQualifiedName);

            this.Items.Add(new FunctionResultContent(
                functionName: functionName,
                pluginName: pluginName,
                callId: null, // Gemini doesn't provide call IDs
                result: calledToolResult.FunctionResult));
        }
    }

    /// <summary>
    /// Parses a fully qualified function name into plugin name and function name.
    /// </summary>
    private static (string? PluginName, string FunctionName) ParseFullyQualifiedName(string fullyQualifiedName)
    {
        int separatorPos = fullyQualifiedName.IndexOf(GeminiFunction.NameSeparator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            string pluginName = fullyQualifiedName.Substring(0, separatorPos).Trim();
            string functionName = fullyQualifiedName.Substring(separatorPos + GeminiFunction.NameSeparator.Length).Trim();
            return (pluginName, functionName);
        }

        return (null, fullyQualifiedName);
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

        // Also populate Items collection with FunctionCallContent for compatibility with FunctionChoiceBehavior
        if (this.ToolCalls is not null)
        {
            foreach (var toolCall in this.ToolCalls)
            {
                KernelArguments? arguments = null;
                if (toolCall.Arguments is not null)
                {
                    arguments = new KernelArguments();
                    foreach (var arg in toolCall.Arguments)
                    {
                        arguments[arg.Key] = arg.Value;
                    }
                }

                this.Items.Add(new FunctionCallContent(
                    functionName: toolCall.FunctionName,
                    pluginName: toolCall.PluginName,
                    id: null, // Gemini doesn't provide call IDs
                    arguments: arguments));
            }
        }
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
