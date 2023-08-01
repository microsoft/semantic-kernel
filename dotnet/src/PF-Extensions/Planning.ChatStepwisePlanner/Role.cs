// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

// TODO fix with serialization options not attributes
public enum Role
{
    [JsonPropertyName("user")]
    User,
    [JsonPropertyName("assistant")]
    Assistant
}
