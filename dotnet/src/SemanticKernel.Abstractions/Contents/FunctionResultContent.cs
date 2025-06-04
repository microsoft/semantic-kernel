// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the result of a function call.
/// </summary>
public sealed class FunctionResultContent : KernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? CallId { get; }

    /// <summary>
    /// The plugin name.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? PluginName { get; }

    /// <summary>
    /// The function name.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? FunctionName { get; }

    /// <summary>
    /// The result of the function call, the function invocation exception or the custom error message.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Result { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionResultContent"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="callId">The function call ID.</param>
    /// <param name="result">The function result.</param>
    [JsonConstructor]
    public FunctionResultContent(string? functionName = null, string? pluginName = null, string? callId = null, object? result = null)
    {
        this.FunctionName = functionName;
        this.PluginName = pluginName;
        this.CallId = callId;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCall">The function call.</param>
    /// <param name="result">The function result.</param>
    public FunctionResultContent(FunctionCallContent functionCall, object? result = null)
    {
        this.CallId = functionCall.Id;
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
    /// Creates <see cref="ChatMessageContent"/> and adds the current instance of the class to the <see cref="ChatMessageContent.Items"/> collection.
    /// </summary>
    /// <returns>The <see cref="ChatMessageContent"/> instance.</returns>
    public ChatMessageContent ToChatMessage()
    {
        return new ChatMessageContent(AuthorRole.Tool, [this]);
    }
}
