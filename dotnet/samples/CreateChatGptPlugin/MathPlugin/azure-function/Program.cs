// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Abstractions;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Configurations;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Enums;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;
using Microsoft.SemanticKernel;
using Models;
using Plugins;
using Plugins.AzureFunctions.Extensions;

const string DefaultSemanticFunctionsFolder = "Prompts";
string semanticFunctionsFolder = Environment.GetEnvironmentVariable("SEMANTIC_SKILLS_FOLDER") ?? DefaultSemanticFunctionsFolder;

var host = new HostBuilder()
    .ConfigureFunctionsWorkerDefaults()
    .ConfigureAppConfiguration(configuration =>
    {
        var config = configuration.SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("local.settings.json", optional: true, reloadOnChange: true);
        var builtConfig = config.Build();
    })
    .ConfigureServices((context, services) =>
    {
        services.Configure<JsonSerializerOptions>(options =>
        {
            // `ConfigureFunctionsWorkerDefaults` sets the default to ignore casing already.
            options.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
        });

        services.AddSingleton<IOpenApiConfigurationOptions>(_ =>
        {
            var options = new OpenApiConfigurationOptions()
            {
                Info = new OpenApiInfo()
                {
                    Version = "1.0.0",
                    Title = "My Plugin",
                    Description = "This plugin does..."
                },
                Servers = DefaultOpenApiConfigurationOptions.GetHostNames(),
                OpenApiVersion = OpenApiVersionType.V3,
                //IncludeRequestingHostName = true,
                ForceHttps = false,
                ForceHttp = false,
            };

            return options;
        });
        services
            .AddTransient((providers) =>
            {
                var appSettings = AppSettings.LoadSettings();
                var builder = Kernel.CreateBuilder();
                builder.Services.WithChatCompletionService(appSettings.Kernel);
                builder.Services.AddLogging(loggingBuilder =>
                {
                    loggingBuilder.AddFilter(level => true);
                    loggingBuilder.AddConsole();
                });
                builder.Plugins.AddFromType<MathPlugin>();
                return builder.Build();
            })
            .AddScoped<AIPluginRunner>();
    })
    .Build();

host.Run();
