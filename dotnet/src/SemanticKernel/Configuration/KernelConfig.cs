// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel.Configuration;

/// <summary>
/// Semantic kernel configuration.
/// </summary>
public sealed class KernelConfig
{
    /// <summary>
    /// Global retry logic used for all the backends
    /// </summary>
    public IRetryMechanism RetryMechanism { get => this._retryMechanism; }

    /// <summary>
    /// Add backend configuration for completion and or embeddings.
    /// </summary>
    /// <param name="config">Backend configuration data</param>
    /// <param name="createClientFunc">Delegate to create an instance of completion client</param>
    /// <param name="overwrite">Allow override of a preexisting configuration</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException"></exception>
    public KernelConfig AddBackendConfig(IBackendConfig config, Func<ILogger, ITextCompletionClient>? createClientFunc = null, bool overwrite = false)
    {
        if (config is not ICompletionBackendConfig and not IEmbeddingsBackendConfig)
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"Unsupported backend configuration: {config.Label}, {config.GetType()}");
        }

        if (config is ICompletionBackendConfig completionConfig)
        {
            this.AddCompletionBackendConfig(completionConfig, createClientFunc, overwrite);
        }

        if (config is IEmbeddingsBackendConfig embeddingsConfig)
        {
            this.AddEmbeddingsBackendConfig(embeddingsConfig, overwrite);
        }
        
        return this;
    }

    public KernelConfig AddCompletionBackendConfig(ICompletionBackendConfig completionConfig, Func<ILogger, ITextCompletionClient>? createClientFunc, bool overwrite = false)
    {
        Verify.NotEmpty(completionConfig.Label, "The completion backend label is empty");
        Verify.NotNull(createClientFunc, "Create completion backend client delegate was not provided");

        if (!overwrite && this.CompletionBackends.ContainsKey(completionConfig.Label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"A completion backend already exists for the label: {completionConfig.Label}");
        }

        this.CompletionBackends[completionConfig.Label] = completionConfig;

        if (this.CompletionBackends.Count == 1)
        {
            this._defaultCompletionBackend = completionConfig.Label;
        }

        this.AddCompletionBackendCreateClient(completionConfig, createClientFunc);

        return this;
    }

    public KernelConfig AddEmbeddingsBackendConfig(IEmbeddingsBackendConfig embeddingsConfig, bool overwrite = false)
    {
        Verify.NotEmpty(embeddingsConfig.Label, "The embedding backend label is empty");

        if (!overwrite && this.EmbeddingsBackends.ContainsKey(embeddingsConfig.Label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"An embeddings backend already exists for the label: {embeddingsConfig.Label}");
        }

        this.EmbeddingsBackends[embeddingsConfig.Label] = embeddingsConfig;

        if (this.EmbeddingsBackends.Count == 1)
        {
            this._defaultEmbeddingsBackend = embeddingsConfig.Label;
        }

        return this;
    }

    /// <summary>
    /// Check whether a given completion backend is in the configuration.
    /// </summary>
    /// <param name="label">Name of completion backend to look for.</param>
    /// <param name="condition">Optional condition that must be met for a backend to be deemed present.</param>
    /// <returns><c>true</c> when a completion backend matching the giving label is present, <c>false</c> otherwise.</returns>
    public bool HasCompletionBackend(string label, Func<IBackendConfig, bool>? condition = null)
    {
        return condition == null
            ? this.CompletionBackends.ContainsKey(label)
            : this.CompletionBackends.Any(x => x.Key == label && condition(x.Value));
    }

    /// <summary>
    /// Check whether a given embeddings backend is in the configuration.
    /// </summary>
    /// <param name="label">Name of embeddings backend to look for.</param>
    /// <param name="condition">Optional condition that must be met for a backend to be deemed present.</param>
    /// <returns><c>true</c> when an embeddings backend matching the giving label is present, <c>false</c> otherwise.</returns>
    public bool HasEmbeddingsBackend(string label, Func<IBackendConfig, bool>? condition = null)
    {
        return condition == null
            ? this.EmbeddingsBackends.ContainsKey(label)
            : this.EmbeddingsBackends.Any(x => x.Key == label && condition(x.Value));
    }

    /// <summary>
    /// Set the retry mechanism to use for the kernel.
    /// </summary>
    /// <param name="retryMechanism">Retry mechanism to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig SetRetryMechanism(IRetryMechanism? retryMechanism = null)
    {
        this._retryMechanism = retryMechanism ?? new PassThroughWithoutRetry();
        return this;
    }

    /// <summary>
    /// Set the default completion backend to use for the kernel.
    /// </summary>
    /// <param name="label">Label of completion backend to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested backend doesn't exist.</exception>
    public KernelConfig SetDefaultCompletionBackend(string label)
    {
        if (!this.CompletionBackends.ContainsKey(label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.BackendNotFound,
                $"The completion backend doesn't exist with label: {label}");
        }

        this._defaultCompletionBackend = label;
        return this;
    }

    /// <summary>
    /// Default completion backend.
    /// </summary>
    public string? DefaultCompletionBackend => this._defaultCompletionBackend;

    /// <summary>
    /// Set the default embeddings backend to use for the kernel.
    /// </summary>
    /// <param name="label">Label of embeddings backend to use.</param>
    /// <returns>The updated kernel configuration.</returns>
    /// <exception cref="KernelException">Thrown if the requested backend doesn't exist.</exception>
    public KernelConfig SetDefaultEmbeddingsBackend(string label)
    {
        if (!this.EmbeddingsBackends.ContainsKey(label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.BackendNotFound,
                $"The embeddings backend doesn't exist with label: {label}");
        }

        this._defaultEmbeddingsBackend = label;
        return this;
    }

    /// <summary>
    /// Default embeddings backend.
    /// </summary>
    public string? DefaultEmbeddingsBackend => this._defaultEmbeddingsBackend;

    /// <summary>
    /// Get the completion backend configuration matching the given label or the default if a label is not provided or not found.
    /// </summary>
    /// <param name="label">Optional label of the desired backend.</param>
    /// <returns>The completion backend configuration matching the given label or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable backend is found.</exception>
    public ICompletionBackendConfig GetCompletionBackend(string? label = null)
    {
        if (string.IsNullOrEmpty(label))
        {
            if (this._defaultCompletionBackend == null)
            {
                throw new KernelException(
                    KernelException.ErrorCodes.BackendNotFound,
                    $"A label was not provided and no default completion backend is available.");
            }

            return this.CompletionBackends[this._defaultCompletionBackend];
        }

        if (this.CompletionBackends.TryGetValue(label, out ICompletionBackendConfig value))
        {
            return value;
        }

        if (this._defaultCompletionBackend != null)
        {
            return this.CompletionBackends[this._defaultCompletionBackend];
        }

        throw new KernelException(
            KernelException.ErrorCodes.BackendNotFound,
            $"Completion backend not found with label: {label} and no default completion backend is available.");
    }

    /// <summary>
    /// Get the embeddings backend configuration matching the given label or the default if a label is not provided or not found.
    /// </summary>
    /// <param name="label">Optional label of the desired backend.</param>
    /// <returns>The embeddings backend configuration matching the given label or the default.</returns>
    /// <exception cref="KernelException">Thrown when no suitable backend is found.</exception>
    public IBackendConfig GetEmbeddingsBackend(string? label = null)
    {
        if (string.IsNullOrEmpty(label))
        {
            if (this._defaultEmbeddingsBackend == null)
            {
                throw new KernelException(
                    KernelException.ErrorCodes.BackendNotFound,
                    $"A label was not provided and no default embeddings backend is available.");
            }

            return this.EmbeddingsBackends[this._defaultEmbeddingsBackend];
        }

        if (this.EmbeddingsBackends.TryGetValue(label, out IEmbeddingsBackendConfig value))
        {
            return value;
        }

        if (this._defaultEmbeddingsBackend != null)
        {
            return this.EmbeddingsBackends[this._defaultEmbeddingsBackend];
        }

        throw new KernelException(
            KernelException.ErrorCodes.BackendNotFound,
            $"Embeddings backend not found with label: {label} and no default embeddings backend is available.");
    }

    /// <summary>
    /// Get all completion backends.
    /// </summary>
    /// <returns>IEnumerable of all completion backends in the kernel configuration.</returns>
    public IEnumerable<IBackendConfig> GetAllCompletionBackends()
    {
        return this.CompletionBackends.Select(x => x.Value);
    }

    /// <summary>
    /// Get all embeddings backends.
    /// </summary>
    /// <returns>IEnumerable of all embeddings backends in the kernel configuration.</returns>
    public IEnumerable<IBackendConfig> GetAllEmbeddingsBackends()
    {
        return this.EmbeddingsBackends.Select(x => x.Value);
    }

    /// <summary>
    /// Remove the completion backend with the given label.
    /// </summary>
    /// <param name="label">Label of backend to remove.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig RemoveCompletionBackend(string label)
    {
        this.CompletionBackends.Remove(label);
        if (this._defaultCompletionBackend == label)
        {
            this._defaultCompletionBackend = this.CompletionBackends.Keys.FirstOrDefault();
        }

        return this;
    }

    /// <summary>
    /// Remove the embeddings backend with the given label.
    /// </summary>
    /// <param name="label">Label of backend to remove.</param>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig RemoveEmbeddingsBackend(string label)
    {
        this.EmbeddingsBackends.Remove(label);
        if (this._defaultEmbeddingsBackend == label)
        {
            this._defaultEmbeddingsBackend = this.EmbeddingsBackends.Keys.FirstOrDefault();
        }

        return this;
    }

    /// <summary>
    /// Remove all completion backends.
    /// </summary>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig RemoveAllCompletionBackends()
    {
        this.CompletionBackends.Clear();
        this._defaultCompletionBackend = null;
        return this;
    }

    /// <summary>
    /// Remove all embeddings backends.
    /// </summary>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig RemoveAllEmbeddingBackends()
    {
        this.EmbeddingsBackends.Clear();
        this._defaultEmbeddingsBackend = null;
        return this;
    }

    /// <summary>
    /// Remove all backends.
    /// </summary>
    /// <returns>The updated kernel configuration.</returns>
    public KernelConfig RemoveAllBackends()
    {
        this.RemoveAllCompletionBackends();
        this.RemoveAllEmbeddingBackends();
        return this;
    }

    internal Func<ILogger, ITextCompletionClient>? TryGetCompletionBackendCreateClient<T>(T config) where T : ICompletionBackendConfig
    {
        if (this.CompletionBackendCreateClients.TryGetValue(config.GetType(), out var completionFactory))
        {
            return completionFactory;
        }

        return null;
    }

    #region private

    private Dictionary<string, ICompletionBackendConfig> CompletionBackends { get; set; } = new();
    private Dictionary<string, IEmbeddingsBackendConfig> EmbeddingsBackends { get; set; } = new();
    private Dictionary<Type, Func<ILogger, ITextCompletionClient>> CompletionBackendCreateClients { get; set; } = new();
    private string? _defaultCompletionBackend;
    private string? _defaultEmbeddingsBackend;
    private IRetryMechanism _retryMechanism = new PassThroughWithoutRetry();

    private void AddCompletionBackendCreateClient<T>(T config, Func<ILogger, ITextCompletionClient> createClientFunc) where T : ICompletionBackendConfig
    {
        if (!this.CompletionBackendCreateClients.ContainsKey(config.GetType()))
        {
            this.CompletionBackendCreateClients.Add(config.GetType(), createClientFunc);
        }
    }

    #endregion
}
