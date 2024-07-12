// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Filters;

internal static class ChannelProcessors
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="channel"></param>
    /// <param name="agent"></param>
    /// <param name="messageContent"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static async Task<ChatMessageContent> ProcessManualFunctionCallAsync(
        AgentChannel channel,
        Agent agent,
        ChatMessageContent messageContent,
        CancellationToken cancellationToken)
    {
        FunctionResultContent resultContent;
        FunctionCallContent? functionCallContent = null;

        try
        {
            functionCallContent = messageContent.Items.OfType<FunctionCallContent>().Single(); // %%% CARDINALITY

            if (channel.ManualFunctionCallProcessor == null)
            {
                throw new KernelException("Manual function call processor not available"); // %%% INFO
            }

            KernelAgent kernelAgent = agent as KernelAgent ?? throw new KernelException("Agent must be a KernelAgent to invoke functions."); // %%%

            if (!kernelAgent.Kernel.Plugins.TryGetFunction(functionCallContent.PluginName, functionCallContent.FunctionName, out KernelFunction? function))
            {
                throw new KernelException("Unable to resolve function"); // %%% INFO
            }

            ManualFunctionCallContext context = new(kernelAgent.Kernel, function, functionCallContent.Arguments) { CancellationToken = cancellationToken };

            await channel.ManualFunctionCallProcessor.OnProcessFunctionCallAsync(context).ConfigureAwait(false);

            if (context.Result == null)
            {
                throw new KernelException("Unknown function result"); // %%% INFO
            }

            resultContent = new(functionCallContent, context.Result);
        }
#pragma warning disable CA1031 // Do not catch general exception types
        catch (Exception exception)
#pragma warning restore CA1031 // Do not catch general exception types
        {
            functionCallContent ??= new("unknown function");
            resultContent = new FunctionResultContent(functionCallContent, exception);
        }

        ChatMessageContent resultMessage = resultContent.ToChatMessage();

        await channel.CaptureFunctionResultAsync(resultMessage, cancellationToken).ConfigureAwait(false);

        return resultMessage;
    }

    internal static async Task<ChatMessageContent> ProcessTerminatedFunctionResultAsync(AgentChannel agentChannel, Agent agent, ChatMessageContent message, CancellationToken cancellationToken)
    {
        if (agentChannel.TerminatedFunctionResultProcessor != null)
        {
            TerminatedFunctionResultContext context = new(message.Items.OfType<FunctionResultContent>().ToArray()) { CancellationToken = cancellationToken }; // %%% LINQ

            await agentChannel.TerminatedFunctionResultProcessor.OnProcessTerminatedFunctionResultAsync(context).ConfigureAwait(false);

            return
                new(AuthorRole.Assistant, content: null)
                {
                    //Items = context.FunctionResults, %%% TBD
                };
        }
        // Default logic if no filter
        return
            new(AuthorRole.Assistant, content: message.Content)
            {
                Items = [.. message.Items.OfType<TextContent>().Cast<KernelContent>()],
            };
    }
}
