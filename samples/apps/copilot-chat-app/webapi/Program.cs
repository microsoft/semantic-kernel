// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using SemanticKernel.Service.CopilotChat.Extensions;

namespace SemanticKernel.Service;

/// <summary>
/// Copilot Chat Service
/// </summary>
public sealed class Program
{
    /// <summary>
    /// Entry point
    /// </summary>
    /// <param name="args">Web application command-line arguments.</param>
    // ReSharper disable once InconsistentNaming
    public static async Task Main(string[] args)
    {
        WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

        // Load in configuration settings from appsettings.json, user-secrets, key vaults, etc...
        builder.Host.AddConfiguration();
        builder.WebHost.UseUrls(); // Disables endpoint override warning message when using IConfiguration for Kestrel endpoint.

        // Add in configuration options and Semantic Kernel services.
        builder.Services
            .AddSingleton<ILogger>(sp => sp.GetRequiredService<ILogger<Program>>()) // some services require an un-templated ILogger
            .AddOptions(builder.Configuration)
            .AddSemanticKernelServices();

        // Add CopilotChat services.
        builder.Services
            .AddCopilotChatOptions(builder.Configuration)
            .AddCopilotChatPlannerServices()
            .AddPersistentChatStore()
            .AddUtilities()
            .AddCopilotChatAuthentication(builder.Configuration)
            .AddCopilotChatAuthorization();

        // Add in the rest of the services.
        builder.Services
            .AddApplicationInsightsTelemetry()
            .AddLogging(logBuilder => logBuilder.AddApplicationInsights())
            .AddEndpointsApiExplorer()
            .AddSwaggerGen()
            .AddCors()
            .AddControllers()
            .AddJsonOptions(options =>
            {
                options.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
            });
        builder.Services.AddHealthChecks().AddCheck("Default",
            () => HealthCheckResult.Healthy("Semantic Kernel service up and running"));

        // Configure middleware and endpoints
        WebApplication app = builder.Build();
        app.UseCors();
        app.MapHealthChecks("/healthz");
        app.UseAuthentication();
        app.UseAuthorization();
        app.MapControllers()
            .RequireAuthorization();

        // Enable Swagger for development environments.
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }

        // Start the service
        Task runTask = app.RunAsync();

        // Log the health probe URL for users to validate the service is running.
        try
        {
            string? address = app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()?.Addresses.FirstOrDefault();
            app.Services.GetRequiredService<ILogger>().LogInformation("Health probe: {0}/heaalthz", address);
        }
        catch (ObjectDisposedException)
        {
            // We likely failed startup which disposes 'app.Services' - don't attempt to display the health probe URL.
        }

        // Wait for the service to complete.
        await runTask;
    }
}
