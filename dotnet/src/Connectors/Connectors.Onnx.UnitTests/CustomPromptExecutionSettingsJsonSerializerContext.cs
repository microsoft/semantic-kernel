// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.Connectors.Onnx.UnitTests;

[JsonSerializable(typeof(CustomPromptExecutionSettings))]
internal sealed partial class CustomPromptExecutionSettingsJsonSerializerContext : JsonSerializerContext
{
}
