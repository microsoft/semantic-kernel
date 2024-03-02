// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI.Assistants;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Gpt;

/// <summary>
/// $$$
/// </summary>
public sealed class GptChannel : AgentChannel
{
    private readonly AssistantsClient _client;
    private readonly string _threadId;

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(KernelAgent agent, ChatMessageContent? input, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        if (input != null)
        {
            var userMessage = await this._client.CreateMessageAsync(this._threadId, MessageRole.User, input.Content, fileIds: null, metadata: null, cancellationToken).ConfigureAwait(false);
            yield return input; // $$$ TRANSFORM USERMESSAGE
        }

        var options =
            new CreateRunOptions(agent.Id) // $$$
            {
                OverrideTools =
                {
                    // $$$
                },
            };

        ThreadRun run = await this._client.CreateRunAsync(this._threadId, options, cancellationToken).ConfigureAwait(false);
        while (run.Status != RunStatus.Completed)
        {
            run = await this._client.GetRunAsync(this._threadId, run.Id, cancellationToken).ConfigureAwait(false);
            //RunStepToolCallDetails
            //this._client.SubmitToolOutputsToRunAsync(run, null, cancellationToken).ConfigureAwait(false);
        }

        PageableList<RunStep> steps = await this._client.GetRunStepsAsync(run, cancellationToken: cancellationToken).ConfigureAwait(false);
        foreach (var step in steps)
        {
            RunStepDetails details = step.StepDetails;
            if (details is RunStepMessageCreationDetails messageDetails)
            {
                ThreadMessage message = await this._client.GetMessageAsync(this._threadId, messageDetails.MessageCreation.MessageId, cancellationToken).ConfigureAwait(false);
                var role = new AuthorRole(message.Role.ToString());

                foreach (var content in message.ContentItems)
                {
                    if (content is MessageTextContent contentMessage)
                    {
                        yield return
                            new ChatMessageContent(role, contentMessage.Text); // $$$ ROLE, NAME
                        continue;
                    }
                    if (content is MessageImageFileContent contentImage)
                    {
                        yield return
                            new ChatMessageContent(role, contentImage.FileId); // $$$ ROLE, NAME, FILE HANDLING
                        continue;
                    }
                }
            }
        }
    }

    /// <inheritdoc/>
    public override async Task RecieveAsync(IEnumerable<ChatMessageContent> content, CancellationToken cancellationToken)
    {
        foreach (var message in content)
        {
            if (string.IsNullOrWhiteSpace(message.Content))
            {
                continue;
            }

            string actorName;
            if (message.Role == AuthorRole.Assistant)
            {
                actorName = message.Role.Label; // $$$ ALIAS WITH NAME
            }
            else
            {
                actorName = message.Role.Label;
            }

            await this._client.CreateMessageAsync(
                this._threadId,
                MessageRole.User,
                $"{actorName}: {message.Content}",
                fileIds: null,
                metadata: null,
                cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="client"></param>
    /// <param name="threadId"></param>
    internal GptChannel(AssistantsClient client, string threadId)
    {
        this._client = client;
        this._threadId = threadId;
    }
}
