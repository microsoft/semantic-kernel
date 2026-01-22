// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace SqlServer.ConformanceTests.Support;

#pragma warning disable CA1810 // Initialize all static fields when those fields are declared

internal static class SqlServerTestEnvironment
{
    public static readonly string? ConnectionString;

    public static bool IsConnectionStringDefined => ConnectionString is not null;

    static SqlServerTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SqlServerTestStore>()
            .Build();

        var sqlServerSection = configuration.GetSection("SqlServer");
        ConnectionString = sqlServerSection["ConnectionString"];
    }
}
