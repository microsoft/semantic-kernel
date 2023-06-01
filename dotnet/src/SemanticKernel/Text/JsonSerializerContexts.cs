// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(Plan))]
[JsonSerializable(typeof(PromptTemplateConfig))]
[JsonSerializable(typeof(SKFunction))]
internal sealed partial class CoreSourceGenerationContext : JsonSerializerContext
{
    public static readonly CoreSourceGenerationContext WithGeneralOptions = new(new JsonSerializerOptions(Json.GeneralOptions));
    public static readonly CoreSourceGenerationContext Indented = new(new JsonSerializerOptions { WriteIndented = true });
}

[JsonSourceGenerationOptions(IncludeFields = true)]
[JsonSerializable(typeof(Plan))]
[JsonSerializable(typeof(IEnumerable<KeyValuePair<string, string>>))]
internal sealed partial class IncludeFieldsSourceGenerationContext : JsonSerializerContext
{
}
