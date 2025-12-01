// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace SqlServer.ConformanceTests.Support;

internal static class SqlServerTestEnvironment
{
    public static readonly string? ConnectionString = GetConnectionString();

    public static bool IsConnectionStringDefined => !string.IsNullOrEmpty(ConnectionString);

    private static string? GetConnectionString()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SqlServerTestStore>()
            .Build();

        return configuration.GetSection("SqlServer")["ConnectionString"];
    }
}
