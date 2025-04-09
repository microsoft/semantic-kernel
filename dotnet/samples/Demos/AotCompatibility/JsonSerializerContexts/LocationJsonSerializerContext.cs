// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SemanticKernel.AotCompatibility.Plugins;

namespace SemanticKernel.AotCompatibility.JsonSerializerContexts;

[JsonSerializable(typeof(Location))]
internal sealed partial class LocationJsonSerializerContext : JsonSerializerContext
{
}
