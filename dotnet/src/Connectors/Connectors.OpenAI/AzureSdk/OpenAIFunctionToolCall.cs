// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents an OpenAI function tool call with deserialized function name and arguments.
/// </summary>
public sealed class OpenAIFunctionToolCall
{
    private string? _fullyQualifiedFunctionName;

    /// <summary>Initialize the <see cref="OpenAIFunctionToolCall"/> from a <see cref="ChatCompletionsFunctionToolCall"/>.</summary>
    internal OpenAIFunctionToolCall(ChatCompletionsFunctionToolCall functionToolCall)
    {
        Verify.NotNull(functionToolCall);
        Verify.NotNull(functionToolCall.Name);

        string fullyQualifiedFunctionName = functionToolCall.Name;
        string functionName = fullyQualifiedFunctionName;
        string? arguments = functionToolCall.Arguments;
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
    /// <param name="update">The tool call update to incorporate.</param>
    /// <param name="toolCallIdsByIndex">Lazily-initialized dictionary mapping indices to IDs.</param>
    /// <param name="functionNamesByIndex">Lazily-initialized dictionary mapping indices to names.</param>
    /// <param name="functionArgumentBuildersByIndex">Lazily-initialized dictionary mapping indices to arguments.</param>
    internal static void TrackStreamingToolingUpdate(
        StreamingToolCallUpdate? update,
        ref Dictionary<int, string>? toolCallIdsByIndex,
        ref Dictionary<int, string>? functionNamesByIndex,
        ref Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex)
    {
        if (update is null)
        {
            // Nothing to track.
            return;
        }

        // If we have an ID, ensure the index is being tracked. Even if it's not a function update,
        // we want to keep track of it so we can send back an error.
        if (update.Id is string id)
        {
            (toolCallIdsByIndex ??= new())[update.ToolCallIndex] = id;
        }

        if (update is StreamingFunctionToolCallUpdate ftc)
        {
            // Ensure we're tracking the function's name.
            if (ftc.Name is string name)
            {
                (functionNamesByIndex ??= new())[ftc.ToolCallIndex] = name;
            }

            // Ensure we're tracking the function's arguments.
            if (ftc.ArgumentsUpdate is string argumentsUpdate)
            {
                if (!(functionArgumentBuildersByIndex ??= new()).TryGetValue(ftc.ToolCallIndex, out StringBuilder? arguments))
                {
                    functionArgumentBuildersByIndex[ftc.ToolCallIndex] = arguments = new();
                }

                arguments.Append(argumentsUpdate);
            }
        }
    }

    /// <summary>
    /// Converts the data built up by <see cref="TrackStreamingToolingUpdate"/> into an array of <see cref="ChatCompletionsFunctionToolCall"/>s.
    /// </summary>
    /// <param name="toolCallIdsByIndex">Dictionary mapping indices to IDs.</param>
    /// <param name="functionNamesByIndex">Dictionary mapping indices to names.</param>
    /// <param name="functionArgumentBuildersByIndex">Dictionary mapping indices to arguments.</param>
    internal static ChatCompletionsFunctionToolCall[] ConvertToolCallUpdatesToChatCompletionsFunctionToolCalls(
        ref Dictionary<int, string>? toolCallIdsByIndex,
        ref Dictionary<int, string>? functionNamesByIndex,
        ref Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex)
    {
        ChatCompletionsFunctionToolCall[] toolCalls = Array.Empty<ChatCompletionsFunctionToolCall>();
        if (toolCallIdsByIndex is { Count: > 0 })
        {
            toolCalls = new ChatCompletionsFunctionToolCall[toolCallIdsByIndex.Count];

            int i = 0;
            foreach (KeyValuePair<int, string> toolCallIndexAndId in toolCallIdsByIndex)
            {
                string? functionName = null;
                StringBuilder? functionArguments = null;

                functionNamesByIndex?.TryGetValue(toolCallIndexAndId.Key, out functionName);
                functionArgumentBuildersByIndex?.TryGetValue(toolCallIndexAndId.Key, out functionArguments);

                toolCalls[i] = new ChatCompletionsFunctionToolCall(toolCallIndexAndId.Value, functionName ?? string.Empty, functionArguments?.ToString() ?? string.Empty);
                i++;
            }

            Debug.Assert(i == toolCalls.Length);
        }

        return toolCalls;
    }
}
