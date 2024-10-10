// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.UnitTests.Functions.JsonSerializerContexts;

[JsonSerializable(typeof(int))]
internal sealed partial class PrimitiveTypesJsonSerializerContext : JsonSerializerContext
{
}
