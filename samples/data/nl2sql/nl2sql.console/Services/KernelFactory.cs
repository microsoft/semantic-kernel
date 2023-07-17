// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Services;

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.Data.Nl2Sql.Exceptions;

/// <summary>
/// Responsible for initializing Semantic <see cref="Kernel"/> based on the configuration.
/// </summary>
internal static class KernelFactory
{
    private const string SettingNameApiKey = "AZURE_OPENAI_KEY";
    private const string SettingNameEndpoint = "AZURE_OPENAI_ENDPOINT";
    private const string SettingNameModelCompletion = "AZURE_OPENAI_DEPLOYMENT_NAME";
    private const string SettingNameModelEmbedding = "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME";

    /// <summary>
    /// Penalty for using any model less than GPT4 for SQL generation.
    /// </summary>
    private const string DefaulChatModel = "gpt-4";
    private const string DefaulEmbedModel = "text-embedding-ada-003";

    /// <summary>
    /// Factory method for <see cref="IServiceCollection"/>
    /// </summary>
    public static Func<IServiceProvider, IKernel> Create(IConfiguration configuration)
    {
        return CreateKernel;

        IKernel CreateKernel(IServiceProvider provider)
        {
            var endpoint =
                configuration.GetValue<string>(SettingNameEndpoint) ??
                throw new InvalidConfigurationException("Setting 'Endpoint' not defined in 'AIService' section.");

            var apikey = configuration.GetValue<string>(SettingNameApiKey) ??
                throw new InvalidConfigurationException("Setting 'Key' not defined in 'AIService' section.");

            var modelCompletion = configuration.GetValue<string>(SettingNameModelCompletion);
            var modelEmbedding = configuration.GetValue<string>(SettingNameModelEmbedding);

            var logger = provider.GetService<ILogger<IKernel>>();

            return ConfigureKernel(endpoint, apikey, modelCompletion, modelEmbedding, logger).Build();
        }
    }

    private static KernelBuilder ConfigureKernel(
        string endpoint,
        string apikey,
        string? modelCompletion,
        string? modelEmbedding,
        ILogger<IKernel>? logger)
    {
        var builder = new KernelBuilder();

        if (logger != null)
        {
            builder.WithLogger(logger);
        }

        modelCompletion ??= DefaulChatModel;
        modelEmbedding ??= DefaulEmbedModel;

        builder
            .WithMemoryStorage(new VolatileMemoryStore())
            .WithAzureTextEmbeddingGenerationService(modelEmbedding, endpoint, apikey);

        if (!modelCompletion.StartsWith("gpt", StringComparison.OrdinalIgnoreCase))
        {
            return builder.WithAzureTextCompletionService(modelCompletion, endpoint, apikey);
        }

        return builder.WithAzureChatCompletionService(modelCompletion, endpoint, apikey);
    }
}
