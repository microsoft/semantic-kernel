// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.IntentTriage;

/// <summary>
/// Factory for creating a <see cref="Kernel"/> instance.
/// </summary>
internal static class KernelFactory
{
    /// <summary>
    /// Create a <see cref="Kernel"/> instance configured with a logging
    /// and an <see cref="IChatCompletionService"/>.
    /// </summary>
    /// <remarks>
    /// PLACEHOLDER: Expect the specifics on authentication for a hosted agent to evolve.
    /// </remarks>
    public static Kernel CreateKernel(IntentTriageServiceSettings settings, ILoggerFactory loggerFactory)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        // Define the logging services
        builder.Services.AddSingleton(loggerFactory);

        // Configure a chat-completion service
        if (!string.IsNullOrEmpty(settings.ApiKey))
        {
            builder.AddAzureOpenAIChatCompletion(
                settings.DeploymentName,
                settings.Endpoint,
                settings.ApiKey);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                settings.DeploymentName,
                settings.Endpoint,
                new AzureCliCredential());
        }

        // Create the kernel
        return builder.Build();
    }
}
