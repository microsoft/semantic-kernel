// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Microsoft.Extensions.Options;

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
    public static async Task Main(string[] args)
    {
        WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

        // Load in configuration settings from appsettings.json, user-secrets, key vaults, etc...
        builder.Host.AddConfiguration();

        // Add in configuration options and Semantic Kernel services.
        builder.Services
            .AddSingleton<ILogger>(sp => sp.GetRequiredService<ILogger<Program>>()) // some services require an untemplated ILogger
            .AddOptions(builder.Configuration)
            .AddSemanticKernelServices()
            .AddPersistentChatStore();

        // Add in the rest of the services.
        builder.Services
            .AddAuthorization(builder.Configuration)
            .AddEndpointsApiExplorer()
            .AddSwaggerGen()
            .AddCors()
            .AddControllers();

        // Configure middleware and endpoints
        WebApplication app = builder.Build();
        app.UseCors();
        app.UseAuthentication();
        app.UseAuthorization();
        app.MapControllers();

        // Enable Swagger for development environments.
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }

        // Start the service
        Task runTask = app.RunAsync();

        // Log the health probe URL for users to validate the service is running.
        string? address = app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()?.Addresses.FirstOrDefault();
        app.Services.GetRequiredService<ILogger>().LogInformation("Health probe: {0}/probe", address);

        // Wait for the service to complete.
        await runTask;
    }
}
