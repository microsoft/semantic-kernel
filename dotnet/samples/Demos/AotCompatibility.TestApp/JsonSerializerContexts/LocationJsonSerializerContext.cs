// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using AotCompatibility.TestApp.Plugins;

namespace AotCompatibility.TestApp.JsonSerializerContexts;

[JsonSerializable(typeof(Location))]
internal sealed partial class LocationJsonSerializerContext : JsonSerializerContext
{
}
