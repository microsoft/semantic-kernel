// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

#pragma warning disable CA1716 // Identifiers should not match keywords

/// <summary>
/// Represents a selector which will return a combination of the containing instances of T and it's pairing <see cref="PromptExecutionSettings"/>
/// from the specified provider based on the model settings.
/// </summary>
[Experimental("SKEXP0001")]
public interface IChatClientSelector
{
    /// <summary>
    /// Resolves an <see cref="IChatClient"/> and associated <see cref="PromptExecutionSettings"/> from the specified
    /// <see cref="Kernel"/> based on a <see cref="KernelFunction"/> and associated <see cref="KernelArguments"/>.
    /// </summary>
    /// <typeparam name="T">
    /// Specifies the type of the <see cref="IChatClient"/> required. This must be the same type
    /// with which the service was registered in the <see cref="IServiceCollection"/> or via
    /// the <see cref="IKernelBuilder"/>.
    /// </typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The function.</param>
    /// <param name="arguments">The function arguments.</param>
    /// <param name="service">The selected service, or null if none was selected.</param>
    /// <param name="serviceSettings">The settings associated with the selected service. This may be null even if a service is selected.</param>
    /// <returns>true if a matching service was selected; otherwise, false.</returns>
    bool TrySelectChatClient<T>(
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments,
        [NotNullWhen(true)] out T? service,
        out PromptExecutionSettings? serviceSettings) where T : class, IChatClient;
}
