// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Services;

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.Data.Nl2Sql.Exceptions;

internal static class KernelFactory
{
    /// <summary>
    /// Penalty for using any model less than GPT4 for SQL generation.
    /// </summary>
    private const string DefaulChatModel = "gpt-4";
    private const string DefaulEmbedModel = "text-embedding-ada-003";

    private const string SectionName = "AIService";
    private const string SettingNameApiKey = "Key";
    private const string SettingNameEndpoint = "Endpoint";
    private const string SettingNameModelCompletion = "CompletionModel";
    private const string SettingNameModelEmbedding = "EmbeddingModel";

    public static Func<IServiceProvider, IKernel> Create(IConfiguration configuration)
    {
        return CreateKernel;

        IKernel CreateKernel(IServiceProvider provider)
        {
            var section =
                configuration.GetSection(SectionName) ??
                throw new InvalidConfigurationException("Section 'AIService' not defined.");

            var endpoint =
                section.GetValue<string>(SettingNameEndpoint) ??
                throw new InvalidConfigurationException("Setting 'Endpoint' not defined in 'AIService' section.");

            var apikey = section.GetValue<string>(SettingNameApiKey) ??
                throw new InvalidConfigurationException("Setting 'Key' not defined in 'AIService' section.");

            var modelCompletion = section.GetValue<string>(SettingNameModelCompletion);
            var modelEmbedding = section.GetValue<string>(SettingNameModelEmbedding);
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
            .WithAzureTextEmbeddingGenerationService(DefaulEmbedModel, endpoint, apikey);

        if (!modelCompletion.StartsWith("gpt", StringComparison.OrdinalIgnoreCase))
        {
            return builder.WithAzureTextCompletionService(modelCompletion, endpoint, apikey);
        }

        return builder.WithAzureChatCompletionService(modelCompletion, endpoint, apikey);
    }
}
