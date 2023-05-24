// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.Options;
using SemanticKernel.Service.Utilities;

namespace SemanticKernel.Service;

internal static class ServicesExtensions
{
    /// <summary>
    /// Parse configuration into options.
    /// </summary>
    internal static IServiceCollection AddOptions(this IServiceCollection services, ConfigurationManager configuration)
    {
        // General configuration
        services.AddOptions<ServiceOptions>()
            .Bind(configuration.GetSection(ServiceOptions.PropertyName))
            .ValidateDataAnnotations()
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        // Default AI service configurations for Semantic Kernel
        services.AddOptions<AIServiceOptions>()
            .Bind(configuration.GetSection(AIServiceOptions.PropertyName))
            .ValidateDataAnnotations()
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        var foo = services.BuildServiceProvider().GetService<IOptions<AIServiceOptions>>();

        // Memory store configuration
        services.AddOptions<MemoriesStoreOptions>()
            .Bind(configuration.GetSection(MemoriesStoreOptions.PropertyName))
            .ValidateDataAnnotations()
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        return services;
    }

    internal static IServiceCollection AddUtilities(this IServiceCollection services)
    {
        return services.AddScoped<AskConverter>();
    }

    /// <summary>
    /// Add CORS settings.
    /// </summary>
    internal static IServiceCollection AddCors(this IServiceCollection services)
    {
        IConfiguration configuration = services.BuildServiceProvider().GetRequiredService<IConfiguration>();
        string[] allowedOrigins = configuration.GetSection("AllowedOrigins").Get<string[]>() ?? Array.Empty<string>();
        if (allowedOrigins.Length > 0)
        {
            services.AddCors(options =>
            {
                options.AddDefaultPolicy(
                    policy =>
                    {
                        policy.WithOrigins(allowedOrigins)
                            .AllowAnyHeader();
                    });
            });
        }

        return services;
    }

    /// <summary>
    /// Trim all string properties, recursively.
    /// </summary>
    private static void TrimStringProperties<T>(T options) where T : class
    {
        Queue<object> targets = new();
        targets.Enqueue(options);

        while (targets.Count > 0)
        {
            object target = targets.Dequeue();
            Type targetType = target.GetType();
            foreach (PropertyInfo property in targetType.GetProperties())
            {
                // Skip enumerations
                if (property.PropertyType.IsEnum)
                {
                    continue;
                }

                // Property is a built-in type, readable, and writable.
                if (property.PropertyType.Namespace == "System" &&
                    property.CanRead &&
                    property.CanWrite)
                {
                    // Property is a non-null string.
                    if (property.PropertyType == typeof(string) &&
                        property.GetValue(target) != null)
                    {
                        property.SetValue(target, property.GetValue(target)!.ToString()!.Trim());
                    }
                }
                else
                {
                    // Property is a non-built-in and non-enum type - queue it for processing.
                    if (property.GetValue(target) != null)
                    {
                        targets.Enqueue(property.GetValue(target)!);
                    }
                }
            }
        }
    }
}
