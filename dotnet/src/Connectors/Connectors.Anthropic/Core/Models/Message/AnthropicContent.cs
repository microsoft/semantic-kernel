// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Claude.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "type")]
[JsonDerivedType(typeof(AnthropicTextContent), typeDiscriminator: "text")]
[JsonDerivedType(typeof(AnthropicTextContent), typeDiscriminator: "text_delta")]
[JsonDerivedType(typeof(AnthropicJsonDeltaContent), typeDiscriminator: "input_json_delta")]
[JsonDerivedType(typeof(AnthropicImageContent), typeDiscriminator: "image")]
[JsonDerivedType(typeof(AnthropicToolCallContent), typeDiscriminator: "tool_use")]
[JsonDerivedType(typeof(AnthropicToolResultContent), typeDiscriminator: "tool_result")]
internal abstract class AnthropicContent;
