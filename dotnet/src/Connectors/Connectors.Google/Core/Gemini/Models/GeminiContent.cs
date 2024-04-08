// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// The base structured datatype containing multi-part content of a message.
/// </summary>
internal sealed class GeminiContent
{
    /// <summary>
    /// Ordered Parts that constitute a single message. Parts may have different MIME types.
    /// </summary>
    [JsonPropertyName("parts")]
    public IList<GeminiPart>? Parts { get; set; }

    /// <summary>
    /// Optional. The producer of the content. Must be either 'user' or 'model' or 'function'.
    /// </summary>
    /// <remarks>Useful to set for multi-turn conversations, otherwise can be left blank or unset.</remarks>
    [JsonPropertyName("role")]
    [JsonConverter(typeof(AuthorRoleConverter))]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public AuthorRole? Role { get; set; }
}
