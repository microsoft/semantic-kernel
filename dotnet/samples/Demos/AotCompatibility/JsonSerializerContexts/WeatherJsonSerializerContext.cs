// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SemanticKernel.AotCompatibility.Plugins;

namespace SemanticKernel.AotCompatibility.JsonSerializerContexts;

[JsonSerializable(typeof(Weather))]
internal sealed partial class WeatherJsonSerializerContext : JsonSerializerContext
{
}
