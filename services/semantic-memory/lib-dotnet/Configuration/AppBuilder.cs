// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;

namespace Microsoft.SemanticKernel.Services.Configuration;

public static class AppBuilder
{
    public static IHost Build(string[]? args = null)
    {
        var builder = Host.CreateApplicationBuilder(args);

        if (Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")?.ToUpperInvariant() == "DEVELOPMENT")
        {
            builder.Configuration.AddJsonFile("appsettings.Development.json", optional: true);
        }

        if (Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")?.ToUpperInvariant() == "PRODUCTION")
        {
            builder.Configuration.AddJsonFile("appsettings.Production.json", optional: true);
        }

        SKMemoryConfig config = builder.Services.UseConfiguration(builder.Configuration);

        builder.Logging.ConfigureLogger();
        builder.Services.UseContentStorage(config);
        builder.Services.UseOrchestrator(config);

        return builder.Build();
    }
}
