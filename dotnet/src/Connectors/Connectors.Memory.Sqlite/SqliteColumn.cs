// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Representation of SQLite column.
/// </summary>
internal sealed class SqliteColumn(
    string name,
    string type,
    bool isPrimary)
{
    public string Name { get; set; } = name;

    public string Type { get; set; } = type;

    public bool IsPrimary { get; set; } = isPrimary;

    public bool HasIndex { get; set; }

    public Dictionary<string, object>? Configuration { get; set; }
}
