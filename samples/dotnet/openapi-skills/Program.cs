using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

// Load configuration
IConfigurationRoot configuration = new ConfigurationBuilder()
    .AddJsonFile(path: "appsettings.json", optional: false, reloadOnChange: true)
    .AddJsonFile(path: "appsettings.Development.json", optional: true, reloadOnChange: true)
    .AddEnvironmentVariables()
    .AddUserSecrets<Program>()
    .Build();

// Initialize logger
using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
{
    builder.AddConfiguration(configuration.GetSection("Logging"))
        .AddConsole()
        .AddDebug();
});

ILogger<Program> logger = loggerFactory.CreateLogger<Program>();

using ILoggerFactory loggerFactory = LoggerFactory.Create(builder => builder.AddConsole());

IKernel kernel = Kernel.Builder
    .WithLogger(loggerFactory.CreateLogger<IKernel>())
    .Build();

kernel.Config.AddAzureChatCompletionService(
