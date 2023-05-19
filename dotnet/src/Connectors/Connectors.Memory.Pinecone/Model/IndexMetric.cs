// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// The vector similarity metric of the index
/// </summary>
/// <value>The vector similarity metric of the index</value>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum IndexMetric
{
    /// <summary>
    /// Default value.
    /// </summary>
    None = 0,

    /// <summary>
    /// Enum Euclidean for value: euclidean
    /// </summary>
    [EnumMember(Value = "euclidean")]
    Euclidean = 1,

    /// <summary>
    /// Enum Cosine for value: cosine
    /// </summary>
    [EnumMember(Value = "cosine")]
    Cosine = 2,

    /// <summary>
    /// Enum Dotproduct for value: dotproduct
    /// </summary>
    [EnumMember(Value = "dotproduct")]
    Dotproduct = 3
}
