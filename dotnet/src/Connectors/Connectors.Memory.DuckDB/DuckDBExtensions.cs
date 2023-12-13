// Copyright (c) Microsoft. All rights reserved.

using System.Data.Common;

namespace Microsoft.SemanticKernel.Connectors.DuckDB;

internal static class DuckDBExtensions
{
    public static T GetFieldValue<T>(this DbDataReader reader, string fieldName)
    {
        int ordinal = reader.GetOrdinal(fieldName);
        return reader.GetFieldValue<T>(ordinal);
    }
}
