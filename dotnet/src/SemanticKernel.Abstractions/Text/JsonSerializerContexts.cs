// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SemanticFunctions;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(IEnumerable<KeyValuePair<string, string>>))]
[JsonSerializable(typeof(IEnumerable<string>))]
[JsonSerializable(typeof(MemoryRecordMetadata))]
[JsonSerializable(typeof(PromptTemplateConfig))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
    public static readonly SourceGenerationContext Indented = new(new() { WriteIndented = true });
    public static readonly SourceGenerationContext WithGeneralOptions = new(new JsonSerializerOptions(Json.GeneralOptions));
}
