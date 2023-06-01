// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(float[]))]
[JsonSerializable(typeof(IEnumerable<float>))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
}
