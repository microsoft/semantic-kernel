// Copyright (c) Microsoft. All rights reserved.

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

        // Add services to the DI container
        AddServices(builder.Services, builder.Configuration);

        var app = builder.Build();

        // Configure the HTTP request pipeline
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }
        app.UseHttpsRedirection();
        // app.UseAuthentication();
        app.UseAuthorization();
        app.MapControllers();

        app.Run();
    }

    private static void AddServices(IServiceCollection services, ConfigurationManager configuration)
    {
        /*builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
            .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));
        builder.Services.AddAuthorization();*/
	
        services.AddControllers();
        // Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
        services.AddEndpointsApiExplorer();
        services.AddSwaggerGen();

        services.AddSingleton<IConfiguration>(configuration);

        services.AddSingleton<ILogger>(s => s.GetRequiredService<ILogger<Kernel>>()); // To support ILogger (as opposed to generic ILogger<T>)

        services.AddSemanticKernelServices(configuration);
    }

    private static void AddSemanticKernelServices(this IServiceCollection services, ConfigurationManager configuration)
    {
        // Each REST call gets a fresh new SK instance
        var kernelConfig = new KernelConfig();
        AIServiceConfig completionConfig = configuration.GetRequiredSection("CompletionConfig").Get<AIServiceConfig>();
        kernelConfig.AddCompletionBackend(completionConfig);
        ISemanticTextMemory memory = NullMemory.Instance;
        AIServiceConfig embeddingConfig = configuration.GetSection("EmbeddingConfig").Get<AIServiceConfig>();
        if (embeddingConfig.IsValid())
        {
            // The same SK memory store is shared with all REST calls and users
            IMemoryStore<float> memoryStore = new VolatileMemoryStore();
            IEmbeddingGeneration<string, float> embeddingGenerator = embeddingConfig.ToTextEmbeddingsService(/* TODO: add logger - Might need to make SK classes more amenable to DI to do this... */);
            kernelConfig.AddEmbeddingBackend(embeddingConfig);
#pragma warning disable CA2000 // Dispose objects before losing scope - Used later through DI
            memory = new SemanticTextMemory(memoryStore, embeddingGenerator);
#pragma warning restore CA2000 // Dispose objects before losing scope
        }
        services.AddSingleton<ISkillCollection, SkillCollection>(); // Keep skill list empty?
        services.AddSingleton<IPromptTemplateEngine, PromptTemplateEngine>();
        services.AddSingleton(memory);
        services.AddSingleton(kernelConfig);

        services.AddScoped<Kernel>();
    }
}
