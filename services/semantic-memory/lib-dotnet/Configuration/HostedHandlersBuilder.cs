// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;

namespace Microsoft.SemanticKernel.Services.Configuration;

public static class HostedHandlersBuilder
{
    public static HostApplicationBuilder CreateApplicationBuilder(string[]? args = null)
    {
        HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

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

        return builder;
    }

    public static void AddHandler<THostedService>(this HostApplicationBuilder builder, string stepName) where THostedService : class, IHostedService, IPipelineStepHandler
    {
        // Register the handler as a hosted service, assigned to a specific pipeline step
        builder.Services.AddHostedService<THostedService>(serviceProvider => ActivatorUtilities.CreateInstance<THostedService>(serviceProvider, stepName));
    }

    public static IHost Build<THostedService>(string stepName, string[]? args = null) where THostedService : class, IHostedService, IPipelineStepHandler
    {
        var builder = CreateApplicationBuilder(args);
        AddHandler<THostedService>(builder, stepName);
        return builder.Build();
    }
}
