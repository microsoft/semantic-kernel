// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.AotTests.Plugins;

namespace SemanticKernel.AotTests.JsonSerializerContexts;

[JsonSerializable(typeof(CustomResult))]
[JsonSerializable(typeof(int))]
[JsonSerializable(typeof(KernelSearchResults<string>))]
[JsonSerializable(typeof(KernelSearchResults<TextSearchResult>))]
[JsonSerializable(typeof(KernelSearchResults<object>))]
internal sealed partial class CustomResultJsonSerializerContext : JsonSerializerContext
{
}
