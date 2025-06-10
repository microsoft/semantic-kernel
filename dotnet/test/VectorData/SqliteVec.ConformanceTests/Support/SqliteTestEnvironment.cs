// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;

namespace SqliteVec.ConformanceTests.Support;

internal static class SqliteTestEnvironment
{
    private static readonly Lazy<bool> s_canUseSqlite = new(CanCreateConnectionAndLoadExtension);

    internal static bool CanUseSqlite => s_canUseSqlite.Value;

    private static bool CanCreateConnectionAndLoadExtension()
    {
        try
        {
            using var connection = new SqliteConnection("Data Source=:memory:;");
            connection.Open();
            connection.LoadVector();
        }
        catch (TypeInitializationException ex)
        {
            Console.WriteLine("Failed to load sqlite native dependency: " + ex.Message);
            return false;
        }
        catch (SqliteException ex)
        {
            Console.WriteLine("Failed to load sqlite_vec extension: " + ex.Message);
            return false;
        }

        return true;
    }
}
