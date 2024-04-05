// Copyright (c) Microsoft. All rights reserved.

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
    [JsonIgnore]
    public string? Id => this.FunctionCall.Id;

    /// <summary>
    /// The plugin name.
    /// </summary>
    [JsonIgnore]
    public string? PluginName => this.FunctionCall.PluginName;

    /// <summary>
    /// The function name.
    /// </summary>
    [JsonIgnore]
    public string FunctionName => this.FunctionCall.FunctionName;

    /// <summary>
    /// The result of the function call.
    /// </summary>
    public object? Result { get; set; }

    /// <summary>
    /// The function call.
    /// </summary>
    public FunctionCallContent FunctionCall { get; private set; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCall">The function call.</param>
    /// <param name="result">The function result.</param>
    [JsonConstructor]
    public FunctionResultContent(FunctionCallContent functionCall, object? result = null)
    {
        Verify.NotNull(functionCall, nameof(functionCall));

        this.FunctionCall = functionCall;
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
}
