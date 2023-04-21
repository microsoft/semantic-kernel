// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Reflection;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Identity.Web;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.Auth;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Skills;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service;

public static class Program
{
    public static void Main(string[] args)
    {
        WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
        builder.Host.ConfigureAppSettings();

        builder.Services
            .AddSingleton<IConfiguration>(builder.Configuration)
            .AddSingleton<ILogger>(sp => sp.GetRequiredService<ILogger<Kernel>>())
            .AddCors()
            .AddAuthorization()
            .AddEndpointsApiExplorer()
            .AddSwaggerGen()
            .AddSemanticKernelServices()
            .AddControllers();

        ServiceConfig serviceConfig = builder.Configuration.GetSection("Service").Get<ServiceConfig>();
        serviceConfig.Validate();

        builder.WebHost.UseUrls($"https://*:{serviceConfig.Port}");

        WebApplication app = builder.Build();

        // Configure the HTTP request pipeline
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }

        app.UseCors();
        app.UseAuthentication();
        app.UseAuthorization();
        app.MapControllers();

        // Log the health probe URL
        app.Services.GetRequiredService<ILogger>().LogInformation(
            "Health probe: https://{Host}:{Port}/probe",
            Dns.GetHostName(),
            serviceConfig.Port);

        app.Run();
    }

    private static IServiceCollection AddCors(this IServiceCollection services)
    {
        var configuration = services.BuildServiceProvider().GetRequiredService<IConfiguration>();
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

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Usage", "CA2208:Instantiate argument exceptions correctly", Justification = "Giving app settings arguments rather than code ones")]
    private static IServiceCollection AddAuthorization(this IServiceCollection services)
    {
        var configuration = services.BuildServiceProvider().GetRequiredService<IConfiguration>();

        var authMethod = configuration.GetSection("Authorization:Type").Get<string>();

        switch (authMethod?.ToUpperInvariant())
        {
            case "AZUREAD":
                services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
                        .AddMicrosoftIdentityWebApi(configuration.GetSection("Authorization:AzureAd"));
                break;

            case "APIKEY":
                services.AddAuthentication(ApiKeyAuthenticationHandler.AuthenticationScheme)
                        .AddScheme<ApiKeyAuthenticationSchemeOptions, ApiKeyAuthenticationHandler>(
                            ApiKeyAuthenticationHandler.AuthenticationScheme,
                            options => options.ApiKey = configuration.GetSection("Authorization:ApiKey").Get<string>());
                break;

            case "NONE":
                services.AddAuthentication(PassThroughAuthenticationHandler.AuthenticationScheme)
                        .AddScheme<AuthenticationSchemeOptions, PassThroughAuthenticationHandler>(
                            PassThroughAuthenticationHandler.AuthenticationScheme, null);
                break;

            default:
                throw new ArgumentException($"Invalid auth method: {authMethod}", "Authorization:Type");
        }

        return services;
    }

    private static IServiceCollection AddSemanticKernelServices(this IServiceCollection services)
    {
        var configuration = services.BuildServiceProvider().GetRequiredService<IConfiguration>();

        // Each API call gets a fresh new SK instance
        services.AddScoped<Kernel>();

        services.AddSingleton<PromptsConfig>(sp =>
        {
            string promptsConfigPath = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "prompts.json");
            PromptsConfig promptsConfig = JsonSerializer.Deserialize<PromptsConfig>(File.ReadAllText(promptsConfigPath)) ??
                                          throw new InvalidOperationException($"Failed to load '{promptsConfigPath}'.");
            promptsConfig.Validate();
            return promptsConfig;
        });

        services.AddSingleton<PromptSettings>();

        // Add a semantic memory store only if we have a valid embedding config
        var embeddingConfig = configuration.GetSection("Embedding").Get<AIServiceConfig>();
        if (embeddingConfig?.IsValid() == true)
        {
            MemoriesStoreConfig memoriesStoreConfig = configuration.GetSection("MemoriesStore").Get<MemoriesStoreConfig>();
            switch (memoriesStoreConfig.Type)
            {
                case MemoriesStoreConfig.MemoriesStoreType.Volatile:
                    services.AddSingleton<IMemoryStore, VolatileMemoryStore>();
                    break;

                case MemoriesStoreConfig.MemoriesStoreType.Qdrant:
                    if (memoriesStoreConfig.Qdrant is null)
                    {
                        throw new InvalidOperationException("MemoriesStore:Qdrant is required when MemoriesStore:Type is 'Qdrant'");
                    }

                    services.AddSingleton<IMemoryStore>(sp => new QdrantMemoryStore(
                        host: memoriesStoreConfig.Qdrant.Host,
                        port: memoriesStoreConfig.Qdrant.Port,
                        vectorSize: memoriesStoreConfig.Qdrant.VectorSize,
                        logger: sp.GetRequiredService<ILogger<QdrantMemoryStore>>()));
                    break;

                default:
                    throw new InvalidOperationException($"Invalid 'MemoriesStore' setting '{memoriesStoreConfig.Type}'. Value must be 'volatile' or 'qdrant'");
            }
        }

        services.AddSingleton<IPromptTemplateEngine, PromptTemplateEngine>();

        services.AddScoped<ISkillCollection, SkillCollection>();

        services.AddScoped<KernelConfig>(sp =>
        {
            var kernelConfig = new KernelConfig();
            AIServiceConfig completionConfig = configuration.GetRequiredSection("Completion").Get<AIServiceConfig>();
            kernelConfig.AddCompletionBackend(completionConfig);

            AIServiceConfig embeddingConfig = configuration.GetSection("Embedding").Get<AIServiceConfig>();
            if (embeddingConfig?.IsValid() == true)
            {
                kernelConfig.AddEmbeddingBackend(embeddingConfig);
            }

            return kernelConfig;
        });

        services.AddScoped<ISemanticTextMemory>(sp =>
        {
            var memoryStore = sp.GetService<IMemoryStore>();
            if (memoryStore is not null)
            {
                AIServiceConfig embeddingConfig = configuration.GetSection("Embedding").Get<AIServiceConfig>();
                if (embeddingConfig?.IsValid() == true)
                {
                    var logger = sp.GetRequiredService<ILogger<AIServiceConfig>>();
                    IEmbeddingGeneration<string, float> embeddingGenerator = embeddingConfig.ToTextEmbeddingsService(logger);

                    return new SemanticTextMemory(memoryStore, embeddingGenerator);
                }
            }

            return NullMemory.Instance;
        });

        // Add persistent chat storage
        IStorageContext<ChatSession> chatSessionInMemoryContext;
        IStorageContext<ChatMessage> chatMessageInMemoryContext;

        ChatStoreConfig chatStoreConfig = configuration.GetSection("ChatStore").Get<ChatStoreConfig>();

        switch (chatStoreConfig.Type)
        {
            case ChatStoreConfig.ChatStoreType.Volatile:
                chatSessionInMemoryContext = new VolatileContext<ChatSession>();
                chatMessageInMemoryContext = new VolatileContext<ChatMessage>();
                break;

            case ChatStoreConfig.ChatStoreType.Filesystem:
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

            case ChatStoreConfig.ChatStoreType.Cosmos:
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

            default:
                throw new InvalidOperationException(
                    $"Invalid 'ChatStore' setting 'chatStoreConfig.Type'. Value must be 'volatile', 'filesystem', or 'cosmos'.");
        }

        services.AddSingleton<ChatSessionRepository>(new ChatSessionRepository(chatSessionInMemoryContext));
        services.AddSingleton<ChatMessageRepository>(new ChatMessageRepository(chatMessageInMemoryContext));

        return services;
    }
}
