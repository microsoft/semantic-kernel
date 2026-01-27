// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace PgVector.ConformanceTests.Support;

#pragma warning disable CA1810 // Initialize all static fields when those fields are declared

internal static class PostgresTestEnvironment
{
    public static readonly string? ConnectionString;

    public static bool IsConnectionStringDefined => ConnectionString is not null;

    static PostgresTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<PostgresTestStore>()
            .Build();

        var postgresSection = configuration.GetSection("Postgres");
        ConnectionString = postgresSection["ConnectionString"];
    }
}
