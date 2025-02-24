// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="IChatClientSelector"/>.
/// </summary>
public static class ChatClientSelectorExtensions
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
    /// <param name="selector">The <see cref="IChatClientSelector"/> to use to select a service from the <see cref="Kernel"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The function.</param>
    /// <param name="arguments">The function arguments.</param>
    /// <returns>A tuple of the selected chat client and the settings associated with the service (the settings may be null).</returns>
    /// <exception cref="KernelException">An appropriate service could not be found.</exception>
    public static (T, PromptExecutionSettings?) SelectChatClient<T>(
        this IChatClientSelector selector,
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments)
        where T : class, IChatClient
    {
        Verify.NotNull(selector);
        Verify.NotNull(kernel);
        Verify.NotNull(function);
        Verify.NotNull(arguments);

        if (selector.TrySelectChatClient<T>(
            kernel, function, arguments,
            out T? service, out PromptExecutionSettings? settings))
        {
            return (service, settings);
        }

        var message = new StringBuilder().Append("Required service of type ").Append(typeof(T)).Append(" not registered.");
        if (function.ExecutionSettings is not null)
        {
            string serviceIds = string.Join("|", function.ExecutionSettings.Keys);
            if (!string.IsNullOrEmpty(serviceIds))
            {
                message.Append(" Expected serviceIds: ").Append(serviceIds).Append('.');
            }

            string modelIds = string.Join("|", function.ExecutionSettings.Values.Select(model => model.ModelId));
            if (!string.IsNullOrEmpty(modelIds))
            {
                message.Append(" Expected modelIds: ").Append(modelIds).Append('.');
            }
        }

        throw new KernelException(message.ToString());
    }

    internal static (IAIService, PromptExecutionSettings?) SelectChatClientAsAIService<T>(
        this IChatClientSelector selector,
        Kernel kernel,
        KernelFunction function,
        KernelArguments arguments)
        where T : class, IChatClient
    {
        var (chatClient, executionSettings) = selector.SelectChatClient<T>(kernel, function, arguments);

        Verify.NotNull(chatClient);

        return (new ChatClientAIService(chatClient), executionSettings);
    }
}
