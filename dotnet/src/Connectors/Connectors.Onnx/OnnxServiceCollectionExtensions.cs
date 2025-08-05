// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Onnx;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="IServiceCollection"/> interface to configure ONNX connectors.
/// </summary>
public static class OnnxServiceCollectionExtensions
{
    /// <summary>
    /// Adds the OnnxRuntimeGenAI Chat Completion services to the specified <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">Model Id.</param>
    /// <param name="modelPath">The generative AI ONNX model path for the chat completion service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="providers">Providers</param>
    /// <param name="loggerFactory">Logger factory.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for various aspects of serialization, such as function argument deserialization, function result serialization, logging, etc., of the service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddOnnxRuntimeGenAIChatCompletion(
        this IServiceCollection services,
        string modelId,
        string modelPath,
        string? serviceId = null,
        List<Provider>? providers = null,
        ILoggerFactory? loggerFactory = null,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) => 
            new OnnxRuntimeGenAIChatCompletionService(
                modelId,
                modelPath,
                providers: providers,
                loggerFactory: serviceProvider.GetService<ILoggerFactory>(),
                jsonSerializerOptions));

        return services;
    }

#pragma warning disable CA2000 // Dispose objects before losing scope
    /// <summary>Adds a text embedding generation service using a BERT ONNX model.</summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="onnxModelPath">The path to the ONNX model file.</param>
    /// <param name="vocabPath">The path to the vocab file.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Obsolete("Use AddBertOnnxEmbeddingGenerator instead.")]
    public static IServiceCollection AddBertOnnxTextEmbeddingGeneration(
        this IServiceCollection services,
        string onnxModelPath,
        string vocabPath,
        BertOnnxOptions? options = null,
        string? serviceId = null)
    {
        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(
            serviceId,
            BertOnnxTextEmbeddingGenerationService.Create(onnxModelPath, vocabPath, options));
    }

    /// <summary>Adds a text embedding generation service using a BERT ONNX model.</summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="onnxModelStream">Stream containing the ONNX model. The stream will be read during this call and will not be used after this call's completion.</param>
    /// <param name="vocabStream">Stream containing the vocab file. The stream will be read during this call and will not be used after this call's completion.</param>
    /// <param name="options">Options for the configuration of the model and service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Obsolete("Use AddBertOnnxEmbeddingGenerator instead.")]
    public static IServiceCollection AddBertOnnxTextEmbeddingGeneration(
        this IServiceCollection services,
        Stream onnxModelStream,
        Stream vocabStream,
        BertOnnxOptions? options = null,
        string? serviceId = null)
    {
        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(
            serviceId,
            BertOnnxTextEmbeddingGenerationService.Create(onnxModelStream, vocabStream, options));
    }
#pragma warning restore CA2000 // Dispose objects before losing scope
}
