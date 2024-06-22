// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// A tool to be used in the chat completion request.
/// </summary>
internal sealed class MistralTool
{
    /// <summary>
    /// The type of the tool. Currently, only function is supported.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; }

    /// <summary>
    /// The associated function.
    /// </summary>
    [JsonPropertyName("function")]
    public MistralFunction Function { get; set; }

    /// <summary>
    /// Construct an instance of <see cref="MistralTool"/>.
    /// </summary>
    [JsonConstructorAttribute]
    public MistralTool(string type, MistralFunction function)
    {
        this.Type = type;
        this.Function = function;
    }
}
