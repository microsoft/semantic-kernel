// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlClient;
using VectorData.ConformanceTests.Xunit;

namespace SqlServer.ConformanceTests.Support;

/// <summary>
/// Skips the test(s) when the database is not Azure SQL Database or SQL database in Microsoft Fabric.
/// This is used for tests that require Azure SQL features not available in on-prem SQL Server (e.g. DiskAnn vector indexes).
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class AzureSqlRequiredAttribute : Attribute, ITestCondition
{
    private static bool? s_isAzureSql;

    public async ValueTask<bool> IsMetAsync()
    {
        if (s_isAzureSql is not null)
        {
            return s_isAzureSql.Value;
        }

        var connectionString = SqlServerTestStore.Instance.ConnectionString;

        using var connection = new SqlConnection(connectionString);
        await connection.OpenAsync();

        using var command = connection.CreateCommand();
        command.CommandText = "SELECT SERVERPROPERTY('EngineEdition')";
        var result = await command.ExecuteScalarAsync();
        var engineEdition = Convert.ToInt32(result);

        // 5 = Azure SQL Database, 11 = SQL database in Microsoft Fabric
        s_isAzureSql = engineEdition is 5 or 11;
        return s_isAzureSql.Value;
    }

    public string SkipReason
        => "This test requires Azure SQL Database or SQL database in Microsoft Fabric.";
}
