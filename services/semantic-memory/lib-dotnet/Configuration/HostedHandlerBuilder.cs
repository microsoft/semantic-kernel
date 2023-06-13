// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace Microsoft.SemanticKernel.Services.Configuration;

public static class HostedHandlerBuilder
{
    public static IHost Build<THostedService>(string[]? args = null) where THostedService : class, IHostedService
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

        // Register the handler as a hosted service
        builder.Services.AddHostedService<THostedService>();

        return builder.Build();
    }
}