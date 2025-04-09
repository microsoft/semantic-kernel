// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(MemoryRecordMetadata))]
internal sealed partial class MemoryRecordMetadataJsonSerializerContext : JsonSerializerContext
{
}
