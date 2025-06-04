// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace SemanticKernel.UnitTests.Functions.JsonSerializerContexts;

[JsonSerializable(typeof(KernelArguments))]
internal sealed partial class KernelArgumentsJsonSerializerContext : JsonSerializerContext
{
}
