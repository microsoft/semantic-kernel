// Copyright (c) Microsoft. All rights reserved.

using System;
using ChatWithAgent.ApiService.Extensions;
using ChatWithAgent.Configuration;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Defines the Program class containing the application's entry point.
/// </summary>
public static class Program
{
    /// <summary>
    /// The main entry point for the application.
    /// </summary>
    /// <param name="args">The command-line arguments.</param>
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add service defaults & Aspire client integrations.
        builder.AddServiceDefaults();

        builder.Services.AddControllers();

        // Add services to the container.
        builder.Services.AddProblemDetails();

        // Load the host configuration.
        var hostConfig = new HostConfig(builder.Configuration);

        // Add Kernel and required AI services.
        AddKernelAndServices(builder, hostConfig);

        var app = builder.Build();

        // Configure the HTTP request pipeline.
        app.UseExceptionHandler();

        app.MapDefaultEndpoints();

        app.MapControllers();

        app.Run();
    }

    private static void AddKernelAndServices(WebApplicationBuilder builder, HostConfig hostConfig)
    {
        // Add Kernel.
        var kernelBuilder = builder.Services.AddKernel();

        switch (hostConfig.AIChatService)
        {
            case AzureOpenAIChatConfig.ConfigSectionName:
            {
                builder.AddAzureOpenAIServices(hostConfig);
                break;
            }

            default:
                throw new NotSupportedException($"AI service '{hostConfig.AIChatService}' is not supported.");
        }

        // Add chat completion agent.
        kernelBuilder.Services.AddTransient<ChatCompletionAgent>((sp) =>
        {
            return new ChatCompletionAgent()
            {
                Kernel = sp.GetRequiredService<Kernel>(),
                Instructions = "TBD"
            };
        });
    }
}
