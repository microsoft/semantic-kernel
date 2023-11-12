// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// Metadata for an Anthropic request.
/// </summary>
public class AnthropicRequestMetadata
{
    /// <summary>
    /// An external identifier for the user who is associated with the request.
    /// </summary>
    /// <remarks>
    /// This should be a uuid, hash value, or other opaque identifier. Anthropic may use this id to help detect abuse.
    /// Do not include any identifying information such as name, email address, or phone number.
    /// </remarks>
    [JsonPropertyName("user_id")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? UserId { get; set; }
}
