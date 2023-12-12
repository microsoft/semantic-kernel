// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
}
