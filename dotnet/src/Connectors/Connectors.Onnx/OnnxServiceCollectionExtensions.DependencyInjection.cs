// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Microsoft.SemanticKernel.Embeddings;

#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable CS0618 // Type or member is obsolete

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Provides extension methods for the <see cref="IServiceCollection"/> interface to configure ONNX connectors.
/// </summary>
public static class OnnxServiceCollectionExtensions
{
    /// <summary>Adds a text embedding generation service using a BERT ONNX model.</summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="onnxModelPath">The path to the ONNX model file.</param>
    /// <param name="vocabPath">The path to the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddBertOnnxEmbeddingGenerator(
        this IServiceCollection services,
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(
            serviceId,
            BertOnnxTextEmbeddingGenerationService.Create(onnxModelPath, vocabPath, options).AsEmbeddingGenerator());
    }

    /// <summary>Adds a text embedding generation service using a BERT ONNX model.</summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="onnxModelStream">Stream containing the ONNX model. The stream will be read during this call and will not be used after this call's completion.</param>
    /// <param name="vocabStream">Stream containing the vocab file. The stream will be read during this call and will not be used after this call's completion.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddBertOnnxEmbeddingGenerator(
        this IServiceCollection services,
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(
            serviceId,
            BertOnnxTextEmbeddingGenerationService.Create(onnxModelStream, vocabStream, options).AsEmbeddingGenerator());
    }

    /// <summary>
    /// Add OnnxRuntimeGenAI Chat Client to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelPath">The generative AI ONNX model path.</param>
    /// <param name="chatClientOptions">The options for the chat client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOnnxRuntimeGenAIChatClient(
        this IServiceCollection services,
        string modelPath,
        OnnxRuntimeGenAIChatClientOptions? chatClientOptions = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelPath);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var chatClient = new OnnxRuntimeGenAIChatClient(modelPath, chatClientOptions ?? new OnnxRuntimeGenAIChatClientOptions()
            {
                PromptFormatter = DefaultPromptFormatter
            });

            var builder = chatClient.AsBuilder()
                .UseKernelFunctionInvocation(loggerFactory);

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build();
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    /// <summary>
    /// Add OnnxRuntimeGenAI Chat Client to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelPath">The generative AI ONNX model path.</param>
    /// <param name="providers">The providers to use for the chat client.</param>
    /// <param name="chatClientOptions">The options for the chat client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOnnxRuntimeGenAIChatClient(
        this IServiceCollection services,
        string modelPath,
        IEnumerable<Provider> providers,
        OnnxRuntimeGenAIChatClientOptions? chatClientOptions = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelPath);
        Verify.NotNull(providers);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var config = new Config(modelPath);
            config.ClearProviders();
            foreach (Provider provider in providers)
            {
                config.AppendProvider(provider.Id);
                foreach (KeyValuePair<string, string> option in provider.Options)
                {
                    config.SetProviderOption(provider.Id, option.Key, option.Value);
                }
            }

            var chatClient = new OnnxRuntimeGenAIChatClient(config, true, chatClientOptions ?? new OnnxRuntimeGenAIChatClientOptions()
            {
                PromptFormatter = DefaultPromptFormatter
            });

            var builder = chatClient.AsBuilder()
                .UseKernelFunctionInvocation(loggerFactory);

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build();
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }

    private static string DefaultPromptFormatter(IEnumerable<ChatMessage> messages, ChatOptions? options)
    {
        StringBuilder promptBuilder = new();
        foreach (var message in messages)
        {
            promptBuilder.Append($"<|{message.Role}|>\n{message.Text}");
        }
        promptBuilder.Append("<|end|>\n<|assistant|>");

        return promptBuilder.ToString();
    }
}
