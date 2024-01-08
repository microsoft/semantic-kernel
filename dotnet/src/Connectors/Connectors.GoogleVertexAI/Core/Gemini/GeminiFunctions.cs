// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// A Tool is a piece of code that enables the system to interact with external systems to perform an action,
/// or set of actions, outside of knowledge and scope of the model.
/// </summary>
internal sealed class GeminiTool
{
    /// <summary>
    /// A list of FunctionDeclarations available to the model that can be used for function calling.
    /// </summary>
    /// <remarks>
    /// The model or system does not execute the function. Instead the defined function may be returned as a
    /// [FunctionCall][content.part.function_call] with arguments to the client side for execution.
    /// The model may decide to call a subset of these functions by populating
    /// [FunctionCall][content.part.function_call] in the response. The next conversation turn may contain
    /// a [FunctionResponse][content.part.function_response] with the [content.role] "function" generation context for the next model turn.
    /// </remarks>
    [JsonPropertyName("functionDeclarations")]
    public IList<GeminiToolFunctionDeclaration> Functions { get; set; }
}

/// <summary>
/// Structured representation of a function declaration as defined by the OpenAPI 3.03 specification.
/// Included in this declaration are the function name and parameters.
/// This FunctionDeclaration is a representation of a block of code that can be used as a Tool by the model and executed by the client.
/// </summary>
internal sealed class GeminiToolFunctionDeclaration
{
    /// <summary>
    /// Required. Name of function.<br />
    /// Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 63.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; }

    /// <summary>
    /// Required. A brief description of the function.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; }

    /// <summary>
    /// Optional. Describes the parameters to this function.
    /// Reflects the Open API 3.03 Parameter Object string Key: the name of the parameter.
    /// Parameter names are case sensitive. Schema Value: the Schema defining the type used for the parameter.
    /// </summary>
    [JsonPropertyName("schema")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiToolFunctionSchema? Schema { get; set; }
}

/// <summary>
/// The Schema object allows the definition of input and output data types.
/// These types can be objects, but also primitives and arrays.
/// Represents a select subset of an OpenAPI 3.0 schema object.
/// </summary>
internal sealed class GeminiToolFunctionSchema
{
    /// <summary>
    /// Required. Data type.
    /// </summary>
    [JsonPropertyName("type")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public GeminiToolFunctionType Type { get; set; }

    /// <summary>
    /// Optional. The format of the data. This is used only for primitive datatypes.
    /// Supported formats: for NUMBER type: float, double for INTEGER type: int32, int64
    /// </summary>
    [JsonPropertyName("format")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Format { get; set; }

    /// <summary>
    /// Optional. A brief description of the parameter. This could contain examples of use.
    /// </summary>
    [JsonPropertyName("description")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Description { get; set; }

    /// <summary>
    /// Optional. Indicates if the value may be null.
    /// </summary>
    [JsonPropertyName("nullable")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? Nullable { get; set; }

    /// <summary>
    /// Optional. Possible values of the element of Type.STRING with enum format.
    /// </summary>
    [JsonPropertyName("enum")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public ISet<string>? Enum { get; set; }

    /// <summary>
    /// Optional. Properties of Type.OBJECT. An object containing a list of "key": value pairs.
    /// </summary>
    [JsonPropertyName("properties")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IDictionary<string, GeminiToolFunctionSchema>? Properties { get; set; }

    /// <summary>
    /// Optional. Required properties of Type.OBJECT.
    /// </summary>
    [JsonPropertyName("required")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<string>? Required { get; set; }

    /// <summary>
    /// Optional. Schema of the elements of Type.ARRAY.
    /// </summary>
    [JsonPropertyName("items")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiToolFunctionSchema? Items { get; set; }
}

/// <summary>
/// Type contains the list of OpenAPI data types as defined by https://spec.openapis.org/oas/v3.0.3#data-types
/// </summary>
[SuppressMessage("ReSharper", "InconsistentNaming")]
internal enum GeminiToolFunctionType
{
    /// <summary>
    /// Not specified, should not be used.
    /// </summary>
    TYPE_UNSPECIFIED,
    STRING,
    NUMBER,
    INTEGER,
    BOOLEAN,
    ARRAY,
    OBJECT,
}
