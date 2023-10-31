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
}
