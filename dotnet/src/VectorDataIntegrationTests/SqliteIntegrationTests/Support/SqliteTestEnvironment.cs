// Copyright (c) Microsoft. All rights reserved.

using System.Data;
using Microsoft.Data.Sqlite;

namespace SqliteIntegrationTests.Support;

internal static class SqliteTestEnvironment
{
    /// <summary>
    /// SQLite extension name for vector search.
    /// More information here: <see href="https://github.com/asg017/sqlite-vec"/>.
    /// </summary>
    private const string VectorSearchExtensionName = "vec0";

    private static bool? s_isSqliteVecInstalled;

    internal static bool TryLoadSqliteVec(SqliteConnection connection)
    {
        if (!s_isSqliteVecInstalled.HasValue)
        {
            if (connection.State != ConnectionState.Open)
            {
                throw new ArgumentException("Connection must be open");
            }

            try
            {
                connection.LoadExtension(VectorSearchExtensionName);
                s_isSqliteVecInstalled = true;
            }
            catch (SqliteException)
            {
                s_isSqliteVecInstalled = false;
            }
        }

        return s_isSqliteVecInstalled.Value;
    }

    internal static bool IsSqliteVecInstalled
    {
        get
        {
            if (!s_isSqliteVecInstalled.HasValue)
            {
                using var connection = new SqliteConnection("Data Source=:memory:;");
                connection.Open();

                s_isSqliteVecInstalled = TryLoadSqliteVec(connection);
            }

            return s_isSqliteVecInstalled.Value;
        }
    }
}
