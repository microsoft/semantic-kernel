// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(JsonObject))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
    public static readonly SourceGenerationContext WithGeneralOptions = new(new JsonSerializerOptions(Json.GeneralOptions));
}
