// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Defines Environment
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum PineconeEnvironment
{
    /// <summary>
    /// Enum UsWest1Gcp for value: us-west1-gcp
    /// </summary>
    [EnumMember(Value = "us-west1-gcp")]
    UsWest1Gcp = 1,

    /// <summary>
    /// Enum UsWest4Gcp for value: us-west4-gcp
    /// </summary>
    [EnumMember(Value = "us-west4-gcp")]
    UsWest4Gcp = 2,

    /// <summary>
    /// Enum UsCentral1Gcp for value: us-central1-gcp
    /// </summary>
    [EnumMember(Value = "us-central1-gcp")]
    UsCentral1Gcp = 3,

    /// <summary>
    /// Enum UsEast1Gcp for value: us-east1-gcp
    /// </summary>
    [EnumMember(Value = "us-east1-gcp")]
    UsEast1Gcp = 4,

    /// <summary>
    /// Enum UsEast4Gcp for value: us-east4-gcp
    /// </summary>
    [EnumMember(Value = "us-east4-gcp")]
    UsEast4Gcp = 5,

    /// <summary>
    /// Enum EuWest1Gcp for value: eu-west1-gcp
    /// </summary>
    [EnumMember(Value = "eu-west1-gcp")]
    EuWest1Gcp = 6,

    /// <summary>
    /// Enum UsEast1Aws for value: us-east1-aws
    /// </summary>
    [EnumMember(Value = "us-east1-aws")]
    UsEast1Aws = 7

}
