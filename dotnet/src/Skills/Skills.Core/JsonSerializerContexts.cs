// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(IEnumerable<string>))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
}
