// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

// For mapping string[] properties to SQL Server JSON columns
[JsonSerializable(typeof(string[]))]
[JsonSerializable(typeof(List<string>))]
internal partial class SqlServerJsonSerializerContext : JsonSerializerContext;
