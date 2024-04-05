// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Claude.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "type")]
[JsonDerivedType(typeof(ClaudeTextContent), typeDiscriminator: "text")]
[JsonDerivedType(typeof(ClaudeImageContent), typeDiscriminator: "image")]
[JsonDerivedType(typeof(ClaudeToolCallContent), typeDiscriminator: "tool_use")]
[JsonDerivedType(typeof(ClaudeToolResultContent), typeDiscriminator: "tool_result")]
internal abstract class ClaudeMessageContent { }
