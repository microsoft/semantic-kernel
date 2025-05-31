// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

// Note: this is temporary - SQL Server will switch away from using JSON arrays to represent embeddings in the future.
[JsonSerializable(typeof(float[]))]
[JsonSerializable(typeof(ReadOnlyMemory<float>))]
internal partial class SqlServerJsonSerializerContext : JsonSerializerContext;
