// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Claude.
/// </summary>
[HackyJsonDerived(typeof(AnthropicTextContent), typeDiscriminator: "text")]
[HackyJsonDerived(typeof(AnthropicDeltaTextContent), typeDiscriminator: "text_delta")]
[HackyJsonDerived(typeof(AnthropicDeltaJsonContent), typeDiscriminator: "input_json_delta")]
[HackyJsonDerived(typeof(AnthropicImageContent), typeDiscriminator: "image")]
internal abstract class AnthropicContent;
