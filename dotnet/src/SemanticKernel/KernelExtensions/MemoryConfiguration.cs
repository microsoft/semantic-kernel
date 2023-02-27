// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.KernelExtensions;

/// <summary>
/// Kernel extension to configure the semantic memory with custom settings
/// </summary>
public static class MemoryConfiguration
{
    /// <summary>
    /// Set the semantic memory to use the given memory storage. Uses the kernel's default embeddings backend.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="storage">Memory storage</param>
    public static void UseMemory(this IKernel kernel, IMemoryStore<float> storage)
    {
        UseMemory(kernel, kernel.Config.DefaultEmbeddingsBackend, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embeddings backend.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingsBackendName">Kernel backend for embedding generation</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope",
        Justification = "The embeddingGenerator object is disposed by the kernel")]
    public static void UseMemory(this IKernel kernel, string? embeddingsBackendName, IMemoryStore<float> storage)
    {
        Verify.NotEmpty(embeddingsBackendName, "The embedding backend name is empty");

        BackendConfig embeddingsBackendCfg = kernel.Config.GetEmbeddingsBackend(embeddingsBackendName);

        IEmbeddingGenerator<string, float>? embeddingGenerator;

        switch (embeddingsBackendCfg.BackendType)
        {
            case BackendTypes.AzureOpenAI:
                Verify.NotNull(embeddingsBackendCfg.AzureOpenAI, "Azure OpenAI configuration is missing");
                embeddingGenerator = new AzureTextEmbeddings(
                    embeddingsBackendCfg.AzureOpenAI.DeploymentName,
                    embeddingsBackendCfg.AzureOpenAI.Endpoint,
                    embeddingsBackendCfg.AzureOpenAI.APIKey,
                    embeddingsBackendCfg.AzureOpenAI.APIVersion,
                    kernel.Log);
                break;

            case BackendTypes.OpenAI:
                Verify.NotNull(embeddingsBackendCfg.OpenAI, "OpenAI configuration is missing");
                embeddingGenerator = new OpenAITextEmbeddings(
                    embeddingsBackendCfg.OpenAI.ModelId,
                    embeddingsBackendCfg.OpenAI.APIKey,
                    embeddingsBackendCfg.OpenAI.OrgId,
                    kernel.Log);
                break;

            default:
                throw new AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    $"Unknown/unsupported backend type {embeddingsBackendCfg.BackendType:G}, unable to prepare semantic memory");
        }

        UseMemory(kernel, embeddingGenerator, storage);
    }

    /// <summary>
    /// Set the semantic memory to use the given memory storage and embedding generator.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="embeddingGenerator">Embedding generator</param>
    /// <param name="storage">Memory storage</param>
    [SuppressMessage("Reliability", "CA2000:Dispose objects before losing scope", Justification = "The embeddingGenerator object is disposed by the kernel")]
    public static void UseMemory(this IKernel kernel, IEmbeddingGenerator<string, float> embeddingGenerator, IMemoryStore<float> storage)
    {
        Verify.NotNull(storage, "The storage instance provided is NULL");
        Verify.NotNull(embeddingGenerator, "The embedding generator is NULL");

        kernel.RegisterMemory(new SemanticTextMemory(storage, embeddingGenerator));
    }
}
