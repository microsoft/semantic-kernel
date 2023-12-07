// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Input variable for prompt functions.
/// </summary>
public sealed class InputVariable
{
    /// <summary>
    /// Name of the variable to pass to the prompt function.
    /// e.g. when using "{{$input}}" the name is "input", when using "{{$style}}" the name is "style", etc.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Variable description for UI applications and planners. Localization is not supported here.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Default value when nothing is provided.
    /// </summary>
    [JsonPropertyName("default")]
    public string Default { get; set; } = string.Empty;

    /// <summary>
    /// True to indicate the input variable is required. True by default.
    /// </summary>
    [JsonPropertyName("is_required")]
    public bool IsRequired { get; set; } = true;

    /// <summary>
    /// JsonSchema describing this variable.
    /// </summary>
    /// <remarks>
    /// This string will be deserialized into an instance of <see cref="KernelJsonSchema"/>.
    /// </remarks>
    [JsonPropertyName("json_schema")]
    public string? JsonSchema { get; set; }
}
