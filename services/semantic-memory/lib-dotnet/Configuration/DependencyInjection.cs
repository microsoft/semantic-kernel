// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services.Storage.ContentStorage;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;
using Microsoft.SemanticKernel.Services.Storage.Queue;

namespace Microsoft.SemanticKernel.Services.Configuration;

public static class DependencyInjection
{
    public static void ConfigureLogger(this ILoggingBuilder builder)
    {
        // Note: log level is set via config file

        builder.ClearProviders();
        builder.AddConsole();
    }

    public static SKMemoryConfig UseConfiguration(this IServiceCollection services, ConfigurationManager mgr)
    {
        SKMemoryConfig config = mgr.GetSection("SKMemory").Get<SKMemoryConfig>()!;
        services.AddSingleton(config);
        return config;
    }

    public static void UseContentStorage(this IServiceCollection services, SKMemoryConfig config)
    {
        const string AzureBlobs = "AZUREBLOBS";
        const string FileSystem = "FILESYSTEM";

        switch (config.ContentStorage.Type.ToUpperInvariant())
        {
            case AzureBlobs:
                services.UseAzureBlobStorage(config);
                break;

            case FileSystem:
                services.AddTransient<IContentStorage>(serviceProvider => new FileSystem(config.ContentStorage.FileSystem.Directory));
                break;

            default:
                throw new NotImplementedException($"Content storage type '{config.ContentStorage.Type}' not available");
        }
    }

    public static void UseOrchestrator(this IServiceCollection services, SKMemoryConfig config)
    {
        const string InProcess = "INPROCESS";
        const string Distributed = "DISTRIBUTED";

        services.AddSingleton<IMimeTypeDetection, MimeTypesDetection>();

        switch (config.Orchestration.Type.ToUpperInvariant())
        {
            case InProcess:
                services.AddSingleton<IPipelineOrchestrator, InProcessPipelineOrchestrator>();
                break;

            case Distributed:
                services.AddSingleton<IPipelineOrchestrator, DistributedPipelineOrchestrator>();
                services.UseDistributedPipeline(config);
                break;

            default:
                throw new NotImplementedException($"Orchestration type '{config.Orchestration}' not available");
        }
    }

    public static void UseAzureBlobStorage(this IServiceCollection services, SKMemoryConfig config)
    {
        const string AzureIdentity = "AZUREIDENTITY";
        const string ConnectionString = "CONNECTIONSTRING";

        // Make configuration available
        services.AddSingleton(config.ContentStorage.AzureBlobs);

        switch (config.ContentStorage.AzureBlobs.Auth.ToUpperInvariant())
        {
            case AzureIdentity:
                services.AddSingleton<IContentStorage>(serviceProvider => new AzureBlob(
                    config.ContentStorage.AzureBlobs.Account,
                    config.ContentStorage.AzureBlobs.EndpointSuffix,
                    serviceProvider.GetService<ILogger<AzureBlob>>()));
                break;

            case ConnectionString:
                services.AddSingleton<IContentStorage>(serviceProvider => new AzureBlob(
                    config.ContentStorage.AzureBlobs.ConnectionString,
                    config.ContentStorage.AzureBlobs.Container,
                    serviceProvider.GetService<ILogger<AzureBlob>>()));
                break;

            default:
                throw new NotImplementedException($"Azure Blob auth type '{config.ContentStorage.AzureBlobs.Auth}' not available");
        }
    }

    public static void UseDistributedPipeline(this IServiceCollection services, SKMemoryConfig config)
    {
        const string AzureQueue = "AZUREQUEUE";
        const string RabbitMQ = "RABBITMQ";
        const string FileBasedQueue = "FILEBASEDQUEUE";

        // Factory for multiple queues
        services.AddSingleton<QueueClientFactory>(
            serviceProvider => new QueueClientFactory(() => serviceProvider.GetService<IQueue>()!));

        // Choose a Queue backend
        switch (config.Orchestration.DistributedPipeline.Type.ToUpperInvariant())
        {
            case AzureQueue:
                const string AzureIdentity = "AZUREIDENTITY";
                const string ConnectionString = "CONNECTIONSTRING";

                // Make configuration available
                services.AddSingleton(config.Orchestration.DistributedPipeline.AzureQueue);

                switch (config.Orchestration.DistributedPipeline.AzureQueue.Auth.ToUpperInvariant())
                {
                    case AzureIdentity:
                        services.AddTransient<IQueue>(serviceProvider => new AzureQueue(
                            config.Orchestration.DistributedPipeline.AzureQueue.Account,
                            config.Orchestration.DistributedPipeline.AzureQueue.EndpointSuffix,
                            serviceProvider.GetService<ILogger<AzureQueue>>()));
                        break;

                    case ConnectionString:
                        services.AddTransient<IQueue>(serviceProvider => new AzureQueue(
                            config.Orchestration.DistributedPipeline.AzureQueue.ConnectionString,
                            serviceProvider.GetService<ILogger<AzureQueue>>()));
                        break;

                    default:
                        throw new NotImplementedException($"Azure Queue auth type '{config.Orchestration.DistributedPipeline.AzureQueue.Auth}' not available");
                }

                break;

            case RabbitMQ:

                // Make configuration available
                services.AddSingleton(config.Orchestration.DistributedPipeline.RabbitMq);

                services.AddTransient<IQueue>(serviceProvider => new RabbitMqQueue(
                    config.Orchestration.DistributedPipeline.RabbitMq.Host,
                    config.Orchestration.DistributedPipeline.RabbitMq.Port,
                    config.Orchestration.DistributedPipeline.RabbitMq.Username,
                    config.Orchestration.DistributedPipeline.RabbitMq.Password,
                    serviceProvider.GetService<ILogger<RabbitMqQueue>>()!));
                break;

            case FileBasedQueue:

                // Make configuration available
                services.AddSingleton(config.Orchestration.DistributedPipeline.FileBasedQueue);

                services.AddTransient<IQueue>(serviceProvider => new FileBasedQueue(
                    config.Orchestration.DistributedPipeline.FileBasedQueue.Path,
                    serviceProvider.GetService<ILogger<FileBasedQueue>>()!));
                break;

            default:
                throw new NotImplementedException($"Queue type '{config.Orchestration.DistributedPipeline.Type}' not available");
        }
    }
}
