// Copyright (c) Microsoft. All rights reserved.

using System.Data.Common;

namespace Microsoft.SemanticKernel.Connectors.Memory.DuckDB;

internal static class DuckDBExtensions
{
    public static string GetString(this DbDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.GetString(ordinal);
    }

    public static float GetFloat(this DbDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.GetFloat(ordinal);
    }

    public static object GetValue(this DbDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.GetValue(ordinal);
    }

    public static bool IsDBNull(this DbDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.IsDBNull(ordinal);
    }
}
