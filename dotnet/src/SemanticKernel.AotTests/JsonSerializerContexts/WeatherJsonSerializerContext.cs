// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.JsonSerializerContexts;

[JsonSerializable(typeof(Weather))]
internal sealed partial class WeatherJsonSerializerContext : JsonSerializerContext
{
}
