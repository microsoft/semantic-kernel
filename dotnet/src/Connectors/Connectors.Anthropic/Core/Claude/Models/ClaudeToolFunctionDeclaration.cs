// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// A Tool is a piece of code that enables the system to interact with external systems to perform an action,
/// or set of actions, outside of knowledge and scope of the model.
/// Structured representation of a function declaration as defined by the OpenAPI 3.03 specification.
/// Included in this declaration are the function name and parameters.
/// This FunctionDeclaration is a representation of a block of code that can be used as a Tool by the model and executed by the client.
/// </summary>
internal sealed class ClaudeToolFunctionDeclaration
{
    /// <summary>
    /// Required. Name of function.
    /// </summary>
    /// <remarks>
    /// Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 63.
    /// </remarks>
    [JsonPropertyName("name")]
    public string Name { get; set; } = null!;

    /// <summary>
    /// Required. A brief description of the function.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = null!;

    /// <summary>
    /// Optional. Describes the parameters to this function.
    /// Reflects the Open API 3.03 Parameter Object string Key: the name of the parameter.
    /// Parameter names are case-sensitive. Schema Value: the Schema defining the type used for the parameter.
    /// </summary>
    [JsonPropertyName("parameters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public JsonNode? Parameters { get; set; }
}
