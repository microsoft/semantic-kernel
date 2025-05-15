// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

internal static class SqliteExtensions
{
    public static T GetFieldValue<T>(this SqliteDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.GetFieldValue<T>(ordinal);
    }

    public static string GetString(this SqliteDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.GetString(ordinal);
    }
}
