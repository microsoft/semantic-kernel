// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.SqlServer;

namespace SqlServerIntegrationTests.Support;

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
            .AddUserSecrets<SqlServerVectorStore>()
            .Build();

        return configuration.GetSection("SqlServer")["ConnectionString"];
    }
}
