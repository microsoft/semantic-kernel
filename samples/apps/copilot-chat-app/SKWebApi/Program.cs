// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.Config;

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
            serverPort = SKWebApiConstants.DefaultServerPort;
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
            logger.LogWarning("Server is using HTTP instead of HTTPS. Do not use HTTP in production." +
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
        // Add memory store only if we have a valid embedding config
        AIServiceConfig embeddingConfig = configuration.GetSection("EmbeddingConfig").Get<AIServiceConfig>();
        if (embeddingConfig?.IsValid() == true)
        {
            services.AddSingleton<IMemoryStore, VolatileMemoryStore>();
        }

        services.AddSingleton<IPromptTemplateEngine, PromptTemplateEngine>();

        services.AddScoped<ISkillCollection, SkillCollection>();

        services.AddScoped<KernelConfig>(sp =>
        {
            var kernelConfig = new KernelConfig();
            AIServiceConfig completionConfig = configuration.GetRequiredSection("CompletionConfig").Get<AIServiceConfig>();
            kernelConfig.AddCompletionBackend(completionConfig);

            AIServiceConfig embeddingConfig = configuration.GetSection("EmbeddingConfig").Get<AIServiceConfig>();
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
                AIServiceConfig embeddingConfig = configuration.GetSection("EmbeddingConfig").Get<AIServiceConfig>();
                if (embeddingConfig?.IsValid() == true)
                {
                    var logger = sp.GetRequiredService<ILogger<AIServiceConfig>>();
                    IEmbeddingGeneration<string, float> embeddingGenerator = embeddingConfig.ToTextEmbeddingsService(logger);

                    return new SemanticTextMemory(memoryStore, embeddingGenerator);
                }
            }

            return NullMemory.Instance;
        });

        // Each REST call gets a fresh new SK instance
        services.AddScoped<Kernel>();
    }
}
