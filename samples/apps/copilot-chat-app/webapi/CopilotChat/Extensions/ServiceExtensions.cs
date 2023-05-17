// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.CopilotChat.Config;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Extensions;

/// <summary>
/// Extension methods for <see cref="IServiceCollection"/>.
/// Add options and services for Copilot Chat.
/// </summary>
public static class CopilotChatServiceExtensions
{
    /// <summary>
    /// Parse configuration into options.
    /// </summary>
    public static IServiceCollection AddCopilotChatOptions(this IServiceCollection services, ConfigurationManager configuration)
    {
        // AI service configurations for Copilot Chat.
        // They are using the same configuration section as Semantic Kernel.
        services.AddOptions<AIServiceOptions>(AIServiceOptions.CompletionPropertyName)
            .Bind(configuration.GetSection(AIServiceOptions.CompletionPropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        services.AddOptions<AIServiceOptions>(AIServiceOptions.EmbeddingPropertyName)
            .Bind(configuration.GetSection(AIServiceOptions.EmbeddingPropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        // Chat log storage configuration
        services.AddOptions<ChatStoreOptions>()
            .Bind(configuration.GetSection(ChatStoreOptions.PropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        // Azure speech token configuration
        services.AddOptions<AzureSpeechOptions>()
            .Bind(configuration.GetSection(AzureSpeechOptions.PropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        // Bot schema configuration
        services.AddOptions<BotSchemaOptions>()
            .Bind(configuration.GetSection(BotSchemaOptions.PropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        // Document memory options
        services.AddOptions<DocumentMemoryOptions>()
            .Bind(configuration.GetSection(DocumentMemoryOptions.PropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        // Planner options
        services.AddOptions<PlannerOptions>()
            .Bind(configuration.GetSection(PlannerOptions.PropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        services.AddOptions<PromptsOptions>()
            .Bind(configuration.GetSection(PromptsOptions.PropertyName))
            .ValidateOnStart()
            .PostConfigure(TrimStringProperties);

        return services;
    }

    /// <summary>
    /// Add persistent chat store services.
    /// </summary>
    public static void AddPersistentChatStore(this IServiceCollection services)
    {
        IStorageContext<ChatSession> chatSessionInMemoryContext;
        IStorageContext<ChatMessage> chatMessageInMemoryContext;

        ChatStoreOptions chatStoreConfig = services.BuildServiceProvider().GetRequiredService<IOptions<ChatStoreOptions>>().Value;

        switch (chatStoreConfig.Type)
        {
            case ChatStoreOptions.ChatStoreType.Volatile:
            {
                chatSessionInMemoryContext = new VolatileContext<ChatSession>();
                chatMessageInMemoryContext = new VolatileContext<ChatMessage>();
                break;
            }

            case ChatStoreOptions.ChatStoreType.Filesystem:
            {
                if (chatStoreConfig.Filesystem == null)
                {
                    throw new InvalidOperationException("ChatStore:Filesystem is required when ChatStore:Type is 'Filesystem'");
                }

                string fullPath = Path.GetFullPath(chatStoreConfig.Filesystem.FilePath);
                string directory = Path.GetDirectoryName(fullPath) ?? string.Empty;
                chatSessionInMemoryContext = new FileSystemContext<ChatSession>(
                    new FileInfo(Path.Combine(directory, $"{Path.GetFileNameWithoutExtension(fullPath)}_sessions{Path.GetExtension(fullPath)}")));
                chatMessageInMemoryContext = new FileSystemContext<ChatMessage>(
                    new FileInfo(Path.Combine(directory, $"{Path.GetFileNameWithoutExtension(fullPath)}_messages{Path.GetExtension(fullPath)}")));

                break;
            }

            case ChatStoreOptions.ChatStoreType.Cosmos:
            {
                if (chatStoreConfig.Cosmos == null)
                {
                    throw new InvalidOperationException("ChatStore:Cosmos is required when ChatStore:Type is 'Cosmos'");
                }
#pragma warning disable CA2000 // Dispose objects before losing scope - objects are singletons for the duration of the process and disposed when the process exits.
                chatSessionInMemoryContext = new CosmosDbContext<ChatSession>(
                    chatStoreConfig.Cosmos.ConnectionString, chatStoreConfig.Cosmos.Database, chatStoreConfig.Cosmos.ChatSessionsContainer);
                chatMessageInMemoryContext = new CosmosDbContext<ChatMessage>(
                    chatStoreConfig.Cosmos.ConnectionString, chatStoreConfig.Cosmos.Database, chatStoreConfig.Cosmos.ChatMessagesContainer);
#pragma warning restore CA2000 // Dispose objects before losing scope
                break;
            }

            default:
            {
                throw new InvalidOperationException(
                    $"Invalid 'ChatStore' setting 'chatStoreConfig.Type'.");
            }
        }

        services.AddSingleton<ChatSessionRepository>(new ChatSessionRepository(chatSessionInMemoryContext));
        services.AddSingleton<ChatMessageRepository>(new ChatMessageRepository(chatMessageInMemoryContext));
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
