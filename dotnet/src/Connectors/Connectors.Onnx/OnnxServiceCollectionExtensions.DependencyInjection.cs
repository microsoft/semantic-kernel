// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
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
    /// <param name="modelId">Model Id.</param>
    /// <param name="modelPath">The generative AI ONNX model path.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    [Experimental("SKEXP0010")]
    public static IServiceCollection AddOnnxRuntimeGenAIChatClient(
        this IServiceCollection services,
        string modelId,
        string modelPath,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(modelPath);

        IChatClient Factory(IServiceProvider serviceProvider, object? _)
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            // Create a lazy wrapper that defers the creation of OnnxRuntimeGenAIChatClient
            return new LazyOnnxChatClient(modelPath, loggerFactory);
        }

        services.AddKeyedSingleton<IChatClient>(serviceId, (Func<IServiceProvider, object?, IChatClient>)Factory);

        return services;
    }
}

/// <summary>
/// A lazy wrapper for OnnxRuntimeGenAIChatClient that defers initialization until first use.
/// </summary>
internal sealed class LazyOnnxChatClient : IChatClient, IDisposable
{
    private readonly string _modelPath;
    private readonly ILoggerFactory? _loggerFactory;
    private IChatClient? _chatClient;
    private readonly object _lock = new();

    public LazyOnnxChatClient(string modelPath, ILoggerFactory? loggerFactory)
    {
        this._modelPath = modelPath;
        this._loggerFactory = loggerFactory;
    }

    private IChatClient GetChatClient()
    {
        if (this._chatClient is null)
        {
            lock (this._lock)
            {
                if (this._chatClient is null)
                {
                    var onnxClient = new OnnxRuntimeGenAIChatClient(this._modelPath, new OnnxRuntimeGenAIChatClientOptions()
                    {
                        PromptFormatter = (messages, options) =>
                        {
                            StringBuilder promptBuilder = new();
                            foreach (var message in messages)
                            {
                                promptBuilder.Append($"<|{message.Role}|>\n{message.Text}");
                            }
                            promptBuilder.Append("<|end|>\n<|assistant|>");

                            return promptBuilder.ToString();
                        }
                    });

                    var builder = onnxClient.AsBuilder().UseKernelFunctionInvocation(this._loggerFactory);

                    if (this._loggerFactory is not null)
                    {
                        builder.UseLogging(this._loggerFactory);
                    }

                    this._chatClient = builder.Build();
                }
            }
        }

        return this._chatClient;
    }

    public Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        => this.GetChatClient().GetResponseAsync(messages, options, cancellationToken);

    public IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        => this.GetChatClient().GetStreamingResponseAsync(messages, options, cancellationToken);

    public TService? GetService<TService>(object? serviceKey = null) where TService : class
        => this.GetChatClient().GetService<TService>(serviceKey);

    public object? GetService(Type serviceType, object? serviceKey = null)
        => this.GetChatClient().GetService(serviceType, serviceKey);

    public void Dispose()
    {
        if (this._chatClient is IDisposable disposable)
        {
            disposable.Dispose();
        }
    }
}
