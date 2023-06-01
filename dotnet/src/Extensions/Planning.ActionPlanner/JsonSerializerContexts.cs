// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Planning.Action;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(ActionPlanResponse))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
    public static readonly SourceGenerationContext WithOptions = new(new JsonSerializerOptions
    {
        AllowTrailingCommas = true,
        DictionaryKeyPolicy = null,
        DefaultIgnoreCondition = JsonIgnoreCondition.Never,
        PropertyNameCaseInsensitive = true,
    });
}
