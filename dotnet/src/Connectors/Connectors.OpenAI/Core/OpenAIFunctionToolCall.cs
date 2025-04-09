// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents an OpenAI function tool call with deserialized function name and arguments.
/// </summary>
public sealed class OpenAIFunctionToolCall
{
    private string? _fullyQualifiedFunctionName;

    /// <summary>Initialize the <see cref="OpenAIFunctionToolCall"/> from a <see cref="ChatToolCall "/>.</summary>
    internal OpenAIFunctionToolCall(ChatToolCall functionToolCall)
    {
        Verify.NotNull(functionToolCall);
        Verify.NotNull(functionToolCall.FunctionName);

        string fullyQualifiedFunctionName = functionToolCall.FunctionName;
        string functionName = fullyQualifiedFunctionName;
        string? arguments = functionToolCall.FunctionArguments?.ToString();
        string? pluginName = null;

        int separatorPos = fullyQualifiedFunctionName.IndexOf(OpenAIFunction.NameSeparator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = fullyQualifiedFunctionName.AsSpan(0, separatorPos).Trim().ToString();
            functionName = fullyQualifiedFunctionName.AsSpan(separatorPos + OpenAIFunction.NameSeparator.Length).Trim().ToString();
        }

        this.Id = functionToolCall.Id;
        this._fullyQualifiedFunctionName = fullyQualifiedFunctionName;
        this.PluginName = pluginName;
        this.FunctionName = functionName;
        if (!string.IsNullOrWhiteSpace(arguments))
        {
            this.Arguments = JsonSerializer.Deserialize<Dictionary<string, object?>>(arguments!);
        }
    }

    /// <summary>Gets the ID of the tool call.</summary>
    public string? Id { get; }

    /// <summary>Gets the name of the plugin with which this function is associated, if any.</summary>
    public string? PluginName { get; }

    /// <summary>Gets the name of the function.</summary>
    public string FunctionName { get; }

    /// <summary>Gets a name/value collection of the arguments to the function, if any.</summary>
    public Dictionary<string, object?>? Arguments { get; }

    /// <summary>Gets the fully-qualified name of the function.</summary>
    /// <remarks>
    /// This is the concatenation of the <see cref="PluginName"/> and the <see cref="FunctionName"/>,
    /// separated by <see cref="OpenAIFunction.NameSeparator"/>. If there is no <see cref="PluginName"/>,
    /// this is the same as <see cref="FunctionName"/>.
    /// </remarks>
    public string FullyQualifiedName =>
        this._fullyQualifiedFunctionName ??=
        string.IsNullOrEmpty(this.PluginName) ? this.FunctionName : $"{this.PluginName}{OpenAIFunction.NameSeparator}{this.FunctionName}";

    /// <inheritdoc/>
    public override string ToString()
    {
        var sb = new StringBuilder(this.FullyQualifiedName);

        sb.Append('(');
        if (this.Arguments is not null)
        {
            string separator = "";
            foreach (var arg in this.Arguments)
            {
                sb.Append(separator).Append(arg.Key).Append(':').Append(arg.Value);
                separator = ", ";
            }
        }
        sb.Append(')');

        return sb.ToString();
    }

    /// <summary>
    /// Tracks tooling updates from streaming responses.
    /// </summary>
    /// <param name="updates">The tool call updates to incorporate.</param>
    /// <param name="toolCallIdsByIndex">Lazily-initialized dictionary mapping indices to IDs.</param>
    /// <param name="functionNamesByIndex">Lazily-initialized dictionary mapping indices to names.</param>
    /// <param name="functionArgumentBuildersByIndex">Lazily-initialized dictionary mapping indices to arguments.</param>
    internal static void TrackStreamingToolingUpdate(
        IReadOnlyList<StreamingChatToolCallUpdate>? updates,
        ref Dictionary<int, string>? toolCallIdsByIndex,
        ref Dictionary<int, string>? functionNamesByIndex,
        ref Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex)
    {
        if (updates is null)
        {
            // Nothing to track.
            return;
        }

        foreach (var update in updates)
        {
            // If we have an ID, ensure the index is being tracked. Even if it's not a function update,
            // we want to keep track of it so we can send back an error.
            if (!string.IsNullOrWhiteSpace(update.ToolCallId))
            {
                (toolCallIdsByIndex ??= [])[update.Index] = update.ToolCallId;
            }

            // Ensure we're tracking the function's name.
            if (!string.IsNullOrWhiteSpace(update.FunctionName))
            {
                (functionNamesByIndex ??= [])[update.Index] = update.FunctionName;
            }

            // Ensure we're tracking the function's arguments.
            if (update.FunctionArgumentsUpdate is not null && !update.FunctionArgumentsUpdate.ToMemory().IsEmpty)
            {
                if (!(functionArgumentBuildersByIndex ??= []).TryGetValue(update.Index, out StringBuilder? arguments))
                {
                    functionArgumentBuildersByIndex[update.Index] = arguments = new();
                }

                arguments.Append(update.FunctionArgumentsUpdate.ToString());
            }
        }
    }

    /// <summary>
    /// Converts the data built up by <see cref="TrackStreamingToolingUpdate"/> into an array of <see cref="ChatToolCall"/>s.
    /// </summary>
    /// <param name="toolCallIdsByIndex">Dictionary mapping indices to IDs.</param>
    /// <param name="functionNamesByIndex">Dictionary mapping indices to names.</param>
    /// <param name="functionArgumentBuildersByIndex">Dictionary mapping indices to arguments.</param>
    internal static ChatToolCall[] ConvertToolCallUpdatesToFunctionToolCalls(
        ref Dictionary<int, string>? toolCallIdsByIndex,
        ref Dictionary<int, string>? functionNamesByIndex,
        ref Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex)
    {
        ChatToolCall[] toolCalls = [];
        if (toolCallIdsByIndex is { Count: > 0 })
        {
            toolCalls = new ChatToolCall[toolCallIdsByIndex.Count];

            int i = 0;
            foreach (KeyValuePair<int, string> toolCallIndexAndId in toolCallIdsByIndex)
            {
                string? functionName = null;
                StringBuilder? functionArguments = null;

                functionNamesByIndex?.TryGetValue(toolCallIndexAndId.Key, out functionName);
                functionArgumentBuildersByIndex?.TryGetValue(toolCallIndexAndId.Key, out functionArguments);

                toolCalls[i] = ChatToolCall.CreateFunctionToolCall(toolCallIndexAndId.Value, functionName ?? string.Empty, BinaryData.FromString(functionArguments?.ToString() ?? string.Empty));
                i++;
            }

            Debug.Assert(i == toolCalls.Length);
        }

        return toolCalls;
    }
}
