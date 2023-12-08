// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Assistants.Internal;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Specialization of <see cref="IKernelPlugin"/> for <see cref="IAssistant"/>
/// </summary>
public interface IAssistantPlugin : IKernelPlugin
{
    internal Assistant Assistant { get; }
}

/// <summary>
/// Convenience actions for <see cref="IAssistantPlugin"/>/
/// </summary>
public static class IAssistantPluginExtensions
{
    /// <summary>
    /// Invoke plugin with user input
    /// </summary>
    /// <param name="plugin">The plugin</param>
    /// <param name="input">The user input</param>
    /// <param name="cancellationToken">A cancel token</param>
    /// <returns>The assistant response</returns>
    public static async Task<string> InvokeAsync(this IAssistantPlugin plugin, string input, CancellationToken cancellationToken = default)
    {
        var args = new KernelArguments { { "input", input } };
        var result = await plugin.First().InvokeAsync(plugin.Assistant.Kernel, args, cancellationToken).ConfigureAwait(false);
        var response = result.GetValue<AssistantResponse>()!;

        return response.Message;
    }
}
