// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace CosmosMongoDBIntegrationTests.Support;

#pragma warning disable CA1810 // Initialize all static fields when those fields are declared

public static class CosmosMongoDBTestEnvironment
{
    public static readonly string? ConnectionString;

    public static bool IsConnectionStringDefined => ConnectionString is not null;

    static CosmosMongoDBTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<CosmosConnectionStringRequiredAttribute>()
            .Build();

        ConnectionString = configuration["AzureCosmosDBMongoDB:ConnectionString"];
    }
}
