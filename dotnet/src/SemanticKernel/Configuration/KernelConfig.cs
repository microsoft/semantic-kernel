// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
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
    /// Adds an Azure OpenAI backend to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public KernelConfig AddAzureOpenAICompletionBackend(
        string label, string deploymentName, string endpoint, string apiKey, string apiVersion = "2022-12-01", bool overwrite = false)
    {
        Verify.NotEmpty(label, "The backend label is empty");

        if (!overwrite && this.CompletionBackends.ContainsKey(label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"A completion backend already exists for the label: {label}");
        }

        this.CompletionBackends[label] = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        if (this.CompletionBackends.Count == 1)
        {
            this._defaultCompletionBackend = label;
        }

        return this;
    }

    /// <summary>
    /// Adds the OpenAI completion backend to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public KernelConfig AddOpenAICompletionBackend(
        string label, string modelId, string apiKey, string? orgId = null, bool overwrite = false)
    {
        Verify.NotEmpty(label, "The backend label is empty");

        if (!overwrite && this.CompletionBackends.ContainsKey(label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"A completion backend already exists for the label: {label}");
        }

        this.CompletionBackends[label] = new OpenAIConfig(label, modelId, apiKey, orgId);

        if (this.CompletionBackends.Count == 1)
        {
            this._defaultCompletionBackend = label;
        }

        return this;
    }

    /// <summary>
    /// Adds an Azure OpenAI embeddings backend to the list.
    /// See https://learn.microsoft.com/azure/cognitive-services/openai for service details.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public KernelConfig AddAzureOpenAIEmbeddingsBackend(
        string label, string deploymentName, string endpoint, string apiKey, string apiVersion = "2022-12-01", bool overwrite = false)
    {
        Verify.NotEmpty(label, "The backend label is empty");

        if (!overwrite && this.EmbeddingsBackends.ContainsKey(label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"An embeddings backend already exists for the label: {label}");
        }

        this.EmbeddingsBackends[label] = new AzureOpenAIConfig(label, deploymentName, endpoint, apiKey, apiVersion);

        if (this.EmbeddingsBackends.Count == 1)
        {
            this._defaultEmbeddingsBackend = label;
        }

        return this;
    }

    /// <summary>
    /// Adds the OpenAI embeddings backend to the list.
    /// See https://platform.openai.com/docs for service details.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    /// <param name="overwrite">Whether to overwrite an existing configuration if the same name exists</param>
    /// <returns>Self instance</returns>
    public KernelConfig AddOpenAIEmbeddingsBackend(
        string label, string modelId, string apiKey, string? orgId = null, bool overwrite = false)
    {
        Verify.NotEmpty(label, "The backend label is empty");

        if (!overwrite && this.EmbeddingsBackends.ContainsKey(label))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                $"An embeddings backend already exists for the label: {label}");
        }

        this.EmbeddingsBackends[label] = new OpenAIConfig(label, modelId, apiKey, orgId);

        if (this.EmbeddingsBackends.Count == 1)
        {
            this._defaultEmbeddingsBackend = label;
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
    public IBackendConfig GetCompletionBackend(string? label = null)
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

        if (this.CompletionBackends.TryGetValue(label, out IBackendConfig value))
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

        if (this.EmbeddingsBackends.TryGetValue(label, out IBackendConfig value))
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

    #region private

    private Dictionary<string, IBackendConfig> CompletionBackends { get; set; } = new();
    private Dictionary<string, IBackendConfig> EmbeddingsBackends { get; set; } = new();
    private string? _defaultCompletionBackend;
    private string? _defaultEmbeddingsBackend;
    private IRetryMechanism _retryMechanism = new PassThroughWithoutRetry();

    #endregion
}
