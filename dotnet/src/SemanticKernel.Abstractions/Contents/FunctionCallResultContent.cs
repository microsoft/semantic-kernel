// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the result of a function call.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionCallResultContent : KernelContent
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
    public string? FunctionName { get; }

    /// <summary>
    /// The result of the function call, the function invocation exception or the custom error message.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Result { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallResultContent"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="result">The function result.</param>
    [JsonConstructor]
    public FunctionCallResultContent(string? functionName = null, string? pluginName = null, string? id = null, object? result = null)
    {
        this.FunctionName = functionName;
        this.PluginName = pluginName;
        this.Id = id;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallRequestContent"/> class.
    /// </summary>
    /// <param name="functionCall">The function call.</param>
    /// <param name="result">The function result.</param>
    public FunctionCallResultContent(FunctionCallRequestContent functionCall, object? result = null)
    {
        this.Id = functionCall.Id;
        this.PluginName = functionCall.PluginName;
        this.FunctionName = functionCall.FunctionName;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallRequestContent"/> class.
    /// </summary>
    /// <param name="functionCallContent">The function call content.</param>
    /// <param name="result">The function result.</param>
    public FunctionCallResultContent(FunctionCallRequestContent functionCallContent, FunctionResult result) :
        this(functionCallContent, result.Value)
    {
        this.InnerContent = result;
    }
}
