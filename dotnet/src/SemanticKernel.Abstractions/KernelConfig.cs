// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel configuration.
/// TODO: use .NET ServiceCollection (will require a lot of changes)
/// </summary>
public sealed class KernelConfig
{
    /// <summary>
    /// Factory for creating HTTP handlers.
    /// </summary>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; private set; } = new DefaultHttpRetryHandlerFactory(new HttpRetryConfig());

    /// <summary>
    /// Default HTTP retry configuration for built-in HTTP handler factory.
    /// </summary>
    public HttpRetryConfig DefaultHttpRetryConfig { get; private set; } = new();

    /// <summary>
    /// Text completion service factories
    /// </summary>
    [Obsolete("This property is deprecated and will be removed in one of the next SK SDK versions.")]
    public Dictionary<string, Func<IKernel, ITextCompletion>> TextCompletionServices { get; } = new();

    /// <summary>
    /// Chat completion service factories
    /// </summary>
    [Obsolete("This property is deprecated and will be removed in one of the next SK SDK versions.")]
    public Dictionary<string, Func<IKernel, IChatCompletion>> ChatCompletionServices { get; } = new();

    /// <summary>
    /// Text embedding generation service factories
    /// </summary>
    [Obsolete("This property is deprecated and will be removed in one of the next SK SDK versions.")]
    public Dictionary<string, Func<IKernel, IEmbeddingGeneration<string, float>>> TextEmbeddingGenerationServices { get; } = new();

    /// <summary>
    /// Image generation service factories
    /// </summary>
    [Obsolete("This property is deprecated and will be removed in one of the next SK SDK versions.")]
    public Dictionary<string, Func<IKernel, IImageGeneration>> ImageGenerationServices { get; } = new();

    /// <summary>
    /// Default name used when binding services if the user doesn't provide a custom value
    /// </summary>
    internal string DefaultServiceId => "__SK_DEFAULT";

    /// <summary>
    /// Add to the list a service for text completion, e.g. Azure OpenAI Text Completion.
    /// </summary>
    /// <param name="serviceFactory">Function used to instantiate the service object</param>
    /// <param name="serviceId">Id used to identify the service</param>
    /// <returns>Current object instance</returns>
    /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use one of the WithAIService extension methods in the KernelBuilder class instead.")]
    public KernelConfig AddTextCompletionService(
        Func<IKernel, ITextCompletion> serviceFactory,
        string? serviceId = null)
    {
        if (serviceId != null && serviceId.Equals(this.DefaultServiceId, StringComparison.OrdinalIgnoreCase))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"The service id '{serviceId}' is reserved, please use a different name");
        }

        serviceId ??= this.DefaultServiceId;

        this.TextCompletionServices[serviceId] = serviceFactory;
        if (this.TextCompletionServices.Count == 1)
        {
            this.TextCompletionServices[this.DefaultServiceId] = serviceFactory;
        }

        return this;
    }

    /// <summary>
    /// Add to the list a service for chat completion, e.g. OpenAI ChatGPT.
    /// </summary>
    /// <param name="serviceFactory">Function used to instantiate the service object</param>
    /// <param name="serviceId">Id used to identify the service</param>
    /// <returns>Current object instance</returns>
    /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use one of the WithAIService extension methods in the KernelBuilder class instead.")]
    public KernelConfig AddChatCompletionService(
        Func<IKernel, IChatCompletion> serviceFactory,
        string? serviceId = null)
    {
        if (serviceId != null && serviceId.Equals(this.DefaultServiceId, StringComparison.OrdinalIgnoreCase))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"The service id '{serviceId}' is reserved, please use a different name");
        }

        serviceId ??= this.DefaultServiceId;

        this.ChatCompletionServices[serviceId] = serviceFactory;
        if (this.ChatCompletionServices.Count == 1)
        {
            this.ChatCompletionServices[this.DefaultServiceId] = serviceFactory;
        }

        return this;
    }

    /// <summary>
    /// Add to the list a service for text embedding generation, e.g. Azure OpenAI Text Embedding.
    /// </summary>
    /// <param name="serviceFactory">Function used to instantiate the service object</param>
    /// <param name="serviceId">Id used to identify the service</param>
    /// <returns>Current object instance</returns>
    /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use one of the WithAIService extension methods in the KernelBuilder class instead.")]
    public KernelConfig AddTextEmbeddingGenerationService(
        Func<IKernel, IEmbeddingGeneration<string, float>> serviceFactory,
        string? serviceId = null)
    {
        if (serviceId != null && serviceId.Equals(this.DefaultServiceId, StringComparison.OrdinalIgnoreCase))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"The service id '{serviceId}' is reserved, please use a different name");
        }

        serviceId ??= this.DefaultServiceId;

        this.TextEmbeddingGenerationServices[serviceId] = serviceFactory;
        if (this.TextEmbeddingGenerationServices.Count == 1)
        {
            this.TextEmbeddingGenerationServices[this.DefaultServiceId] = serviceFactory;
        }

        return this;
    }

    /// <summary>
    /// Add to the list a service for image generation, e.g. OpenAI DallE.
    /// </summary>
    /// <param name="serviceFactory">Function used to instantiate the service object</param>
    /// <param name="serviceId">Id used to identify the service</param>
    /// <returns>Current object instance</returns>
    /// <exception cref="KernelException">Failure if a service with the same id already exists</exception>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use one of the WithAIService extension methods in the KernelBuilder class instead.")]
    public KernelConfig AddImageGenerationService(
        Func<IKernel, IImageGeneration> serviceFactory,
        string? serviceId = null)
    {
        if (serviceId != null && serviceId.Equals(this.DefaultServiceId, StringComparison.OrdinalIgnoreCase))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidServiceConfiguration,
                $"The service id '{serviceId}' is reserved, please use a different name");
        }

        serviceId ??= this.DefaultServiceId;

        this.ImageGenerationServices[serviceId] = serviceFactory;
        if (this.ImageGenerationServices.Count == 1)
        {
            this.ImageGenerationServices[this.DefaultServiceId] = serviceFactory;
        }

        return this;
    }

    #region Set

    /// <summary>
    /// Set the http retry handler factory to use for the kernel.
    /// </summary>
    /// <param name="httpHandlerFactory">Http retry handler factory to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig SetHttpRetryHandlerFactory(IDelegatingHandlerFactory? httpHandlerFactory = null)
    {
        if (httpHandlerFactory != null)
        {
            this.HttpHandlerFactory = httpHandlerFactory;
        }

        return this;
    }

    public KernelConfig SetDefaultHttpRetryConfig(HttpRetryConfig? httpRetryConfig)
    {
        if (httpRetryConfig != null)
        {
            this.DefaultHttpRetryConfig = httpRetryConfig;
            this.SetHttpRetryHandlerFactory(new DefaultHttpRetryHandlerFactory(httpRetryConfig));
        }

        return this;
    }

    /// <summary>
    /// Set the default completion service to use for the kernel.
    /// </summary>
    /// <param name="serviceId">Identifier of completion service to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use one of the WithDefaultAIService extension methods in the KernelBuilder class instead.")]
    public KernelConfig SetDefaultTextCompletionService(string serviceId)
    {
        if (!this.TextCompletionServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"A text completion service id '{serviceId}' doesn't exist");
        }

        this.TextCompletionServices[this.DefaultServiceId] = this.TextCompletionServices[serviceId];
        return this;
    }

    /// <summary>
    /// Set the default embedding service to use for the kernel.
    /// </summary>
    /// <param name="serviceId">Identifier of text embedding service to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested service doesn't exist.</exception>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions. Please use one of the WithDefaultAIService extension methods in the KernelBuilder class instead.")]
    public KernelConfig SetDefaultTextEmbeddingGenerationService(string serviceId)
    {
        if (!this.TextEmbeddingGenerationServices.ContainsKey(serviceId))
        {
            throw new KernelException(
                KernelException.ErrorCodes.ServiceNotFound,
                $"A text embedding generation service id '{serviceId}' doesn't exist");
        }

        this.TextEmbeddingGenerationServices[this.DefaultServiceId] = this.TextEmbeddingGenerationServices[serviceId];
        return this;
    }

    #endregion

    #region Remove

    /// <summary>
    /// Remove all text completion services.
    /// </summary>
    /// <returns>The updated kernel configuration.</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions.")]
    public KernelConfig RemoveAllTextCompletionServices()
    {
        this.TextCompletionServices.Clear();
        return this;
    }

    /// <summary>
    /// Remove all chat completion services.
    /// </summary>
    /// <returns>The updated kernel configuration.</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions.")]
    public KernelConfig RemoveAllChatCompletionServices()
    {
        this.ChatCompletionServices.Clear();
        return this;
    }

    /// <summary>
    /// Remove all text embedding generation services.
    /// </summary>
    /// <returns>The updated kernel configuration.</returns>
    [Obsolete("This method is deprecated and will be removed in one of the next SK SDK versions.")]
    public KernelConfig RemoveAllTextEmbeddingGenerationServices()
    {
        this.TextEmbeddingGenerationServices.Clear();
        return this;
    }

    #endregion
}
