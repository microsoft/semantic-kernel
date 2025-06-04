// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.UnitTests.Functions.JsonSerializerContexts;

[JsonSerializable(typeof(TestReturnType))]
internal sealed partial class TestReturnTypeJsonSerializerContext : JsonSerializerContext
{
}
