// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Claude.
/// </summary>
[InternalJsonDerived(typeof(AnthropicTextContent), typeDiscriminator: "text")]
[InternalJsonDerived(typeof(AnthropicDeltaTextContent), typeDiscriminator: "text_delta")]
[InternalJsonDerived(typeof(AnthropicDeltaJsonContent), typeDiscriminator: "input_json_delta")]
[InternalJsonDerived(typeof(AnthropicImageContent), typeDiscriminator: "image")]
internal abstract class AnthropicContent;
