// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Text;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;

public class FewShotExample
{
    [JsonConverter(typeof(JsonStringEnumConverter))]
    [JsonPropertyName("role")]
    public Role Role { get; set; }

    [JsonPropertyName("content")]
    public string? Content { get; set; }
}
