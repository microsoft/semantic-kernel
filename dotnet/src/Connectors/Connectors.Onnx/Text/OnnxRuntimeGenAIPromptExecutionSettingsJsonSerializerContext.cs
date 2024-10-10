// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Onnx;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(OnnxRuntimeGenAIPromptExecutionSettings))]
internal sealed partial class OnnxRuntimeGenAIPromptExecutionSettingsJsonSerializerContext : JsonSerializerContext
{
    public static readonly OnnxRuntimeGenAIPromptExecutionSettingsJsonSerializerContext ReadPermissive = new(new()
    {
        AllowTrailingCommas = true,
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    });
}
