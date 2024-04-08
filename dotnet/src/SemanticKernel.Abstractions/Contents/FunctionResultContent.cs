// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the result of a function call.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionResultContent : KernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Id { get; }

    /// <summary>
    /// The plugin name.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? PluginName { get; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string FunctionName { get; }

    /// <summary>
    /// The result of the function call.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Result { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionResultContent"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="result">The function result.</param>
    [JsonConstructor]
    public FunctionResultContent(string functionName, string? pluginName = null, string? id = null, object? result = null)
    {
        this.FunctionName = functionName;
        this.PluginName = pluginName;
        this.Id = id;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCall">The function call.</param>
    /// <param name="result">The function result.</param>
    public FunctionResultContent(FunctionCallContent functionCall, object? result = null)
    {
        this.Id = functionCall.Id;
        this.PluginName = functionCall.PluginName;
        this.FunctionName = functionCall.FunctionName;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCallContent">The function call content.</param>
    /// <param name="result">The function result.</param>
    public FunctionResultContent(FunctionCallContent functionCallContent, FunctionResult result) :
        this(functionCallContent, result.Value)
    {
        this.InnerContent = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionResultContent"/> class.
    /// </summary>
    /// <param name="fullyQualifiedName">Fully-qualified name of the function.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="result">The function result.</param>
    /// <param name="functionNameSeparator">The function name separator.</param>
    public static FunctionResultContent Create(string fullyQualifiedName, string? id = null, object? result = null, string functionNameSeparator = "-")
    {
        Verify.NotNull(fullyQualifiedName);

        string? pluginName = null;
        string functionName = fullyQualifiedName;

        int separatorPos = fullyQualifiedName.IndexOf(functionNameSeparator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = fullyQualifiedName.AsSpan(0, separatorPos).Trim().ToString();
            functionName = fullyQualifiedName.AsSpan(separatorPos + functionNameSeparator.Length).Trim().ToString();
        }

        return new FunctionResultContent(
            functionName: functionName,
            pluginName: pluginName,
            id: id,
            result: result);
    }
}
