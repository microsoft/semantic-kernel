// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Output variable return from a prompt functions.
/// </summary>
public sealed class OutputVariable
{
    /// <summary>
    /// Variable description for UI applications and planners. Localization is not supported here.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;
}
