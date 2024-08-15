// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Core;

/// <summary>The response format of prompty.</summary>
internal sealed class PromptyResponseFormat
{
    /// <summary>The response format type (e.g: json_object).</summary>
    [YamlMember(Alias = "type")]
    public string? Type { get; set; }
}
