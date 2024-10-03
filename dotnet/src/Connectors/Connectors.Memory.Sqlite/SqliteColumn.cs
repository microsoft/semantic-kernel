// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Representation of SQLite column.
/// </summary>
internal record SqliteColumn(string Name, string Type, bool IsPrimary);
