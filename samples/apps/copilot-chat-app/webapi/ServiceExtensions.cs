// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.Options;
using Microsoft.Identity.Web;
using SemanticKernel.Service.Auth;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Model;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service;

internal static class ServicesExtensions
{
    /// <summary>
    /// Parse configuration into options.
    /// </summary>
    internal static IServiceCollection AddOptions(this IServiceCollection services, ConfigurationManager configuration)
    {
        // General  configuration
        services.AddOptions<ServiceOptions>()
            .Bind(configuration.GetSection(ServiceOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // AI service configurations
        services.AddOptions<AIServiceOptions>(AIServiceOptions.CompletionPropertyName)
            .Bind(configuration.GetSection(AIServiceOptions.CompletionPropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        services.AddOptions<AIServiceOptions>(AIServiceOptions.EmbeddingPropertyName)
            .Bind(configuration.GetSection(AIServiceOptions.EmbeddingPropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // Chat log storage configuration
        services.AddOptions<ChatStoreOptions>()
            .Bind(configuration.GetSection(ChatStoreOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // Memory store configuration
        services.AddOptions<MemoriesStoreOptions>()
            .Bind(configuration.GetSection(MemoriesStoreOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // Azure speech token configuration
        services.AddOptions<AzureSpeechOptions>()
            .Bind(configuration.GetSection(AzureSpeechOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // Bot schema configuration
        services.AddOptions<BotSchemaOptions>()
            .Bind(configuration.GetSection(BotSchemaOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // Document memory options
        services.AddOptions<DocumentMemoryOptions>()
            .Bind(configuration.GetSection(DocumentMemoryOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        // Planner options
        services.AddOptions<PlannerOptions>()
            .Bind(configuration.GetSection(PlannerOptions.PropertyName))
            .ValidateDataAnnotations().ValidateOnStart();

        return services;
    }

    /// <summary>
    /// Add CORS settings.
    /// </summary>
    internal static IServiceCollection AddCors(this IServiceCollection services)
    {
        IConfiguration configuration = services.BuildServiceProvider().GetRequiredService<IConfiguration>();
        string[] allowedOrigins = configuration.GetSection("AllowedOrigins").Get<string[]>();
        if (allowedOrigins is not null && allowedOrigins.Length > 0)
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
    /// Add authorization services
    /// </summary>
    internal static IServiceCollection AddAuthorization(this IServiceCollection services, IConfiguration configuration)
    {
        AuthorizationOptions config = services.BuildServiceProvider().GetRequiredService<IOptions<AuthorizationOptions>>().Value;
        switch (config.Type)
        {
            case AuthorizationOptions.AuthorizationType.AzureAd:
                services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
                    .AddMicrosoftIdentityWebApi(configuration.GetSection($"{AuthorizationOptions.PropertyName}:AzureAd"));
                break;

            case AuthorizationOptions.AuthorizationType.ApiKey:
                services.AddAuthentication(ApiKeyAuthenticationHandler.AuthenticationScheme)
                    .AddScheme<ApiKeyAuthenticationSchemeOptions, ApiKeyAuthenticationHandler>(
                        ApiKeyAuthenticationHandler.AuthenticationScheme,
                        options => options.ApiKey = config.ApiKey);
                break;

            case AuthorizationOptions.AuthorizationType.None:
                services.AddAuthentication(PassThroughAuthenticationHandler.AuthenticationScheme)
                    .AddScheme<AuthenticationSchemeOptions, PassThroughAuthenticationHandler>(
                        authenticationScheme: PassThroughAuthenticationHandler.AuthenticationScheme,
                        configureOptions: null);
                break;

            default:
                throw new InvalidOperationException($"Invalid authorization type '{config.Type}'.");
        }

        return services;
    }

    /// <summary>
    /// Add persistent chat store services.
    /// </summary>
    internal static void AddPersistentChatStore(this IServiceCollection services)
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
}
