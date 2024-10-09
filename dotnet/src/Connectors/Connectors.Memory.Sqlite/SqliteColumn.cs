// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Representation of SQLite column.
/// </summary>
internal sealed record SqliteColumn(
    string Name,
    string Type,
    bool IsPrimary,
    Dictionary<string, object>? Configuration);
