// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planning;
public class FunctionPlanParameter
{
    /// <summary>
    /// Name of the function parameter
    /// </summary>
    [JsonPropertyName("parameterName")]
    public string Name { get; set; } = String.Empty;

    /// <summary>
    /// Value of the function parameter
    /// </summary>
    [JsonPropertyName("value")]
    public string Value { get; set; } = String.Empty;
}
