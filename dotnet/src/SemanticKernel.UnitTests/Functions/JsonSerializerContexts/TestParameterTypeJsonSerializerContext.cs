// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace SemanticKernel.UnitTests.Functions.JsonSerializerContexts;

[JsonSerializable(typeof(TestParameterType))]
internal sealed partial class TestParameterTypeJsonSerializerContext : JsonSerializerContext
{
}
