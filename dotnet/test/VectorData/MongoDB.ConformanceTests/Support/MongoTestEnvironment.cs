// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace MongoDB.ConformanceTests.Support;

#pragma warning disable CA1810 // Initialize all static fields when those fields are declared

internal static class MongoTestEnvironment
{
    public static readonly string? ConnectionUrl;

    public static bool IsConnectionInfoDefined => ConnectionUrl is not null;

    static MongoTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .Build();

        var mongoSection = configuration.GetSection("MongoDB");
        ConnectionUrl = mongoSection["ConnectionURL"];
    }
}
