// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Reflection;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Skills;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service;

public static class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        builder.Host.ConfigureAppSettings();

        // Set port to run on
        string serverPortString = builder.Configuration.GetSection("ServicePort").Get<string>();
        if (!int.TryParse(serverPortString, out int serverPort))
        {
            serverPort = CopilotChatApiConstants.DefaultServerPort;
        }

        // Set the protocol to use
        bool useHttp = builder.Configuration.GetSection("UseHttp").Get<bool>();
        string protocol = useHttp ? "http" : "https";

        builder.WebHost.UseUrls($"{protocol}://*:{serverPort}");

        // Add services to the DI container
        AddServices(builder.Services, builder.Configuration);

        var app = builder.Build();

        var logger = app.Services.GetRequiredService<ILogger>();

        // Configure the HTTP request pipeline
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }

        app.UseCors();
        app.UseAuthorization();
        app.MapControllers();

        // Log the health probe URL
        string hostName = Dns.GetHostName();
        logger.LogInformation("Health probe: {Protocol}://{Host}:{Port}/probe", protocol, hostName, serverPort);

        if (useHttp)
        {
            logger.LogWarning("Server is using HTTP instead of HTTPS. Do not use HTTP in production. " +
                              "All tokens and secrets sent to the server can be intercepted over the network.");
        }

        app.Run();
    }

    private static void AddServices(IServiceCollection services, ConfigurationManager configuration)
    {
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

        services.AddControllers();
        // Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
        services.AddEndpointsApiExplorer();
        services.AddSwaggerGen();

        services.AddSingleton<IConfiguration>(configuration);

        // To support ILogger (as opposed to the generic ILogger<T>)
        services.AddSingleton<ILogger>(sp => sp.GetRequiredService<ILogger<Kernel>>());

        services.AddSemanticKernelServices(configuration);
    }

    private static void AddSemanticKernelServices(this IServiceCollection services, ConfigurationManager configuration)
    {
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
        AIServiceConfig embeddingConfig = configuration.GetSection("Embedding").Get<AIServiceConfig>();
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
    }
}
