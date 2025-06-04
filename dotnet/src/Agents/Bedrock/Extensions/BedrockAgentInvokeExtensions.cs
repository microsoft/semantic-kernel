// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgentRuntime;
using Amazon.BedrockAgentRuntime.Model;
using Amazon.Runtime.EventStreams;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.FunctionCalling;

namespace Microsoft.SemanticKernel.Agents.Bedrock;

/// <summary>
/// Extensions associated with the status of a <see cref="BedrockAgent"/>.
/// </summary>
internal static class BedrockAgentInvokeExtensions
{
    public static async IAsyncEnumerable<ChatMessageContent> InternalInvokeAsync(
        this BedrockAgent agent,
        InvokeAgentRequest invokeAgentRequest,
        KernelArguments? arguments,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        // This session state is used to store the results of function calls to be passed back to the agent.
        // https://docs.aws.amazon.com/sdkfornet/v3/apidocs/items/BedrockAgentRuntime/TSessionState.html
        SessionState? sessionState = null;
        for (var requestIndex = 0; ; requestIndex++)
        {
            if (sessionState != null)
            {
                invokeAgentRequest.SessionState = sessionState;
                sessionState = null;
            }
            var invokeAgentResponse = await agent.RuntimeClient.InvokeAgentAsync(invokeAgentRequest, cancellationToken).ConfigureAwait(false);

            if (invokeAgentResponse.HttpStatusCode != System.Net.HttpStatusCode.OK)
            {
                throw new HttpOperationException($"Failed to invoke agent. Status code: {invokeAgentResponse.HttpStatusCode}");
            }

            List<FunctionCallContent> functionCallContents = [];
            await foreach (var responseEvent in invokeAgentResponse.Completion.ToAsyncEnumerable().ConfigureAwait(false))
            {
                if (responseEvent is BedrockAgentRuntimeEventStreamException bedrockAgentRuntimeEventStreamException)
                {
                    throw new KernelException("Failed to handle Bedrock Agent stream event.", bedrockAgentRuntimeEventStreamException);
                }

                var chatMessageContent =
                    HandleChunkEvent(agent, responseEvent) ??
                    HandleFilesEvent(agent, responseEvent) ??
                    HandleReturnControlEvent(agent, responseEvent, arguments) ??
                    HandleTraceEvent(agent, responseEvent) ??
                    throw new KernelException($"Failed to handle Bedrock Agent stream event: {responseEvent}");
                if (chatMessageContent.Items.Count > 0 && chatMessageContent.Items[0] is FunctionCallContent functionCallContent)
                {
                    functionCallContents.AddRange(chatMessageContent.Items.Where(item => item is FunctionCallContent).Cast<FunctionCallContent>());
                }
                else
                {
                    yield return chatMessageContent;
                }
            }

            // This is used to cap the auto function invocation loop to prevent infinite loops.
            // It doesn't use the the `FunctionCallsProcessor` to process the functions because we do not need 
            // many of the features it offers and we want to keep the code simple.
            var functionChoiceBehaviorConfiguration = new FunctionCallsProcessor().GetConfiguration(
                FunctionChoiceBehavior.Auto(), [], requestIndex, agent.Kernel);

            if (functionCallContents.Count > 0 && functionChoiceBehaviorConfiguration!.AutoInvoke)
            {
                var functionResults = await InvokeFunctionCallsAsync(agent, functionCallContents, cancellationToken).ConfigureAwait(false);
                sessionState = CreateSessionStateWithFunctionResults(functionResults, agent);
            }
            else
            {
                break;
            }
        }
    }

    private static ChatMessageContent? HandleChunkEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        return responseEvent is not PayloadPart payload
            ? null
            : new ChatMessageContent()
            {
                Role = AuthorRole.Assistant,
                AuthorName = agent.GetDisplayName(),
                Content = Encoding.UTF8.GetString(payload.Bytes.ToArray()),
                ModelId = agent.AgentModel.FoundationModel,
                InnerContent = payload,
            };
    }

    private static ChatMessageContent? HandleFilesEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        if (responseEvent is not FilePart files)
        {
            return null;
        }

        ChatMessageContentItemCollection binaryContents = [];
        foreach (var file in files.Files)
        {
            binaryContents.Add(new BinaryContent(file.Bytes.ToArray(), file.Type)
            {
                Metadata = new Dictionary<string, object?>()
                {
                    { "Name", file.Name },
                },
            });
        }

        return new ChatMessageContent()
        {
            Role = AuthorRole.Assistant,
            AuthorName = agent.GetDisplayName(),
            Items = binaryContents,
            ModelId = agent.AgentModel.FoundationModel,
            InnerContent = files,
        };
    }

    private static ChatMessageContent? HandleReturnControlEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent,
        KernelArguments? arguments)
    {
        if (responseEvent is not ReturnControlPayload returnControlPayload)
        {
            return null;
        }

        ChatMessageContentItemCollection functionCallContents = [];
        foreach (var invocationInput in returnControlPayload.InvocationInputs)
        {
            var functionInvocationInput = invocationInput.FunctionInvocationInput;
            functionCallContents.Add(new FunctionCallContent(
                functionInvocationInput.Function,
                id: returnControlPayload.InvocationId,
                arguments: functionInvocationInput.Parameters.FromFunctionParameters(arguments))
            {
                Metadata = new Dictionary<string, object?>()
                {
                    { "ActionGroup", functionInvocationInput.ActionGroup },
                    { "ActionInvocationType", functionInvocationInput.ActionInvocationType },
                },
            });
        }

        return new ChatMessageContent()
        {
            Role = AuthorRole.Assistant,
            AuthorName = agent.GetDisplayName(),
            Items = functionCallContents,
            ModelId = agent.AgentModel.FoundationModel,
            InnerContent = returnControlPayload,
        };
    }

    private static ChatMessageContent? HandleTraceEvent(
        BedrockAgent agent,
        IEventStreamEvent responseEvent)
    {
        return responseEvent is not TracePart trace
            ? null
            : new ChatMessageContent()
            {
                Role = AuthorRole.Assistant,
                AuthorName = agent.GetDisplayName(),
                ModelId = agent.AgentModel.FoundationModel,
                InnerContent = trace,
            };
    }

    private static async Task<List<FunctionResultContent>> InvokeFunctionCallsAsync(
        BedrockAgent agent,
        List<FunctionCallContent> functionCallContents,
        CancellationToken cancellationToken)
    {
        var functionResults = await Task.WhenAll(functionCallContents.Select(async functionCallContent =>
        {
            return await functionCallContent.InvokeAsync(agent.Kernel, cancellationToken).ConfigureAwait(false);
        })).ConfigureAwait(false);

        return [.. functionResults];
    }

    private static SessionState CreateSessionStateWithFunctionResults(List<FunctionResultContent> functionResults, BedrockAgent agent)
    {
        return functionResults.Count == 0
            ? throw new KernelException("No function results were returned.")
            : new()
            {
                InvocationId = functionResults[0].CallId,
                ReturnControlInvocationResults = [.. functionResults.Select(functionResult =>
                    {
                        return new InvocationResultMember()
                        {
                            FunctionResult = new Amazon.BedrockAgentRuntime.Model.FunctionResult
                            {
                                ActionGroup = agent.KernelFunctionActionGroupSignature,
                                Function = functionResult.FunctionName,
                                ResponseBody = new Dictionary<string, ContentBody>
                                {
                                    { "TEXT", new ContentBody() { Body = FunctionCallsProcessor.ProcessFunctionResult(functionResult.Result ?? string.Empty) } }
                                }
                            }
                        };
                    }
                )],
            };
    }
}
