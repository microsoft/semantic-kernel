// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Orchestration.Extensions;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Magentic;

/// <summary>
/// An <see cref="ChatManagerActor"/> used to manage a <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
internal sealed partial class MagenticManagerActor : ChatManagerActor
{
    private readonly State _state;
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="MagenticManagerActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="team">The team of agents being orchestrated</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="groupTopic">The unique topic used to broadcast to the entire chat.</param>
    /// <param name="kernel">A kernel with services used by the manager.</param>
    /// <param name="handoff">Defines how the group-chat is translated into a singular response.</param>
    /// <param name="logger">The logger to use with this actor</param>
    public MagenticManagerActor(AgentId id, IAgentRuntime runtime, ChatGroup team, AgentType orchestrationType, TopicId groupTopic, Kernel kernel, ChatHandoff handoff, ILogger<MagenticManagerActor>? logger = null)
        : base(id, runtime, team, orchestrationType, groupTopic, handoff, logger)
    {
        this._kernel = kernel;
        this._state = new State(this.Team);
    }

    /// <summary>
    /// Settings that define the orchestration behavior.
    /// </summary>
    public MagenticOrchestrationSettings Settings { get; init; } = MagenticOrchestrationSettings.Default;

    /// <inheritdoc/>
    protected override async Task<AgentType?> PrepareTaskAsync()
    {
        ChatHistory internalChat = [];

        await this.AnalyzeFactsAsync(internalChat).ConfigureAwait(false);
        await this.AnalyzePlanAsync(internalChat).ConfigureAwait(false);
        await this.GenerateLedgerAsync(internalChat).ConfigureAwait(false);

        return await this.SelectAgentAsync().ConfigureAwait(false);
    }

    /// <inheritdoc/>
    protected override async Task<AgentType?> SelectAgentAsync()
    {
        int stallCount = 0;
        int retryCount = 0;
        bool isStalled = false;

        do
        {
            string agentName = string.Empty;
            string agentInstruction = string.Empty;
            try
            {
                LedgerStatus status = await this.AnalyzeStatusAsync().ConfigureAwait(false);
                this.Logger.LogTrace("{Json}", status.AsJson()); // %%% LOGGER

                if (status.IsTaskComplete)
                {
                    await this.GenerateHandoffAsync().ConfigureAwait(false);
                    return null;
                }

                isStalled = !status.IsTaskProgressing || status.IsTaskInLoop;
                agentName = status.Name;
                agentInstruction = status.Instruction;
            }
            catch (Exception exception) when (!exception.IsCriticalException())
            {
                this.Logger.LogError(exception, "// %%% LOGGER");
                isStalled = true;
            }

            if (!isStalled && this.Team.ContainsKey(agentName))
            {
                stallCount = Math.Max(0, stallCount - 1);

                ChatMessageContent instruction = new(AuthorRole.Assistant, agentInstruction);
                this.Chat.Add(instruction);
                await this.PublishMessageAsync(instruction.ToGroup(), this.GroupTopic).ConfigureAwait(false); // %%% TARGET AGENT ???

                return agentName;
            }

            isStalled = true;
            ++stallCount;

            Debug.WriteLine($"TASK STALLED: #{stallCount}/{this.Settings.MaximumStallCount} [#{retryCount}]"); // %%% LOGGER

            if (stallCount >= this.Settings.MaximumStallCount)
            {
                if (retryCount >= this.Settings.MaximumRetryCount)
                {
                    await this.PublishMessageAsync(new ChatMessageContent(AuthorRole.User, "I've experienced multiple failures and am unable to continue.").ToGroup(), this.GroupTopic).ConfigureAwait(false);
                    return null;
                }

                retryCount++;
                stallCount = 0;

                Debug.WriteLine($"TASK RESET [#{retryCount}]"); // %%% LOGGER

                await this.PublishMessageAsync(new ChatMessages.Reset(), this.GroupTopic).ConfigureAwait(false);
                await this.UpdateTaskAsync().ConfigureAwait(false);
            }
        }
        while (isStalled);

        return null;
    }

    private async Task UpdateTaskAsync()
    {
        ChatHistory internalChat = [.. this.Chat];
        this.Chat.Clear();

        await this.UpdateFactsAsync(internalChat).ConfigureAwait(false);
        await this.UpdatePlanAsync(internalChat).ConfigureAwait(false);
        await this.GenerateLedgerAsync(internalChat).ConfigureAwait(false);
    }

    private async Task AnalyzeFactsAsync(ChatHistory internalChat)
    {
        if (this._state.Facts != null)
        {
            return;
        }
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Task, this.InputTask.Message },
            };
        this._state.Facts = await this.GetResponseAsync(internalChat, Prompts.NewFactsTemplate, arguments).ConfigureAwait(false);
        Debug.WriteLine($"\n<FACTS>:\n{this._state.Facts}\n</FACTS>\n"); // %%% LOGGER
        //await this.PublishMessageAsync(this._state.Facts.ToProgress("Analyzed task..."), Framework.AgentProxy.InnerChatTopic).ConfigureAwait(false); // %%% PROGRESS
    }

    private async Task UpdateFactsAsync(ChatHistory internalChat)
    {
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Task, this.InputTask.Message },
                { Prompts.Parameters.Facts, this._state.Facts },
            };
        this._state.Facts = await this.GetResponseAsync(internalChat, Prompts.NewFactsTemplate, arguments).ConfigureAwait(false);
        Debug.WriteLine($"\n<FACTS>:\n{this._state.Facts}\n</FACTS>\n"); // %%% LOGGER
        //await this.PublishMessageAsync(this._state.Facts.ToProgress("Analyzed task..."), Framework.AgentProxy.InnerChatTopic).ConfigureAwait(false); // %%% PROGRESS
    }

    private async Task AnalyzePlanAsync(ChatHistory internalChat)
    {
        if (this._state.Plan != null)
        {
            return;
        }
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Team, this._state.Team },
            };
        this._state.Plan = await this.GetResponseAsync(internalChat, Prompts.NewPlanTemplate, arguments).ConfigureAwait(false);
        Debug.WriteLine($"\n<PLAN>:\n{this._state.Plan}\n</PLAN>\n"); // %%% LOGGER
        //await this.PublishMessageAsync(this._state.Plan.ToProgress("Generated plan..."), Framework.AgentProxy.InnerChatTopic).ConfigureAwait(false); // %%% PROGRESS
    }

    private async Task UpdatePlanAsync(ChatHistory internalChat)
    {
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Team, this._state.Team },
            };
        this._state.Plan = await this.GetResponseAsync(internalChat, Prompts.NewPlanTemplate, arguments).ConfigureAwait(false);
        Debug.WriteLine($"\n<PLAN>:\n{this._state.Plan}\n</PLAN>\n"); // %%% LOGGER
        //await this.PublishMessageAsync(this._state.Plan.ToProgress("Generated plan..."), Framework.AgentProxy.InnerChatTopic).ConfigureAwait(false); // %%% PROGRESS
    }

    private async Task GenerateLedgerAsync(ChatHistory internalChat)
    {
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Task, this.InputTask.Message },
                { Prompts.Parameters.Team, this._state.Team },
                { Prompts.Parameters.Facts, this._state.Facts },
                { Prompts.Parameters.Plan, this._state.Plan },
            };
        this._state.Ledger = await this.GetMessageAsync(Prompts.LedgerTemplate, arguments).ConfigureAwait(false);
        this.Chat.Add(this._state.Ledger);
        await this.PublishMessageAsync(this._state.Ledger.ToGroup(), this.GroupTopic).ConfigureAwait(false);
    }

    private async Task<LedgerStatus> AnalyzeStatusAsync()
    {
        ChatHistory internalChat = [.. this.Chat];
        //PromptExecutionSettings executionSettings = new() { ExtensionData = new Dictionary<string, object>() { { "ResponseFormat", typeof(LedgerStatus) } } };
        OpenAIPromptExecutionSettings executionSettings = new() { ResponseFormat = typeof(LedgerStatus) }; // %%% DEPENDENCY TREE
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Task, this.InputTask.Message },
                { Prompts.Parameters.Team, this._state.Team },
                { Prompts.Parameters.Facts, this._state.Facts },
            };
        ChatMessageContent response = await this.GetResponseAsync(internalChat, Prompts.StatusTemplate, arguments, executionSettings).ConfigureAwait(false);
        //await this.PublishMessageAsync(response.ToProgress("Evaluted status..."), Framework.AgentProxy.InnerChatTopic).ConfigureAwait(false);
        LedgerStatus status = response.GetValue<LedgerStatus>();
        Debug.WriteLine(status.AsJson()); // %%% LOGGER
        return status;
    }

    private async Task GenerateHandoffAsync()
    {
        KernelArguments arguments =
            new()
            {
                { Prompts.Parameters.Task, this.InputTask.Message },
            };
        ChatMessageContent response = await this.GetResponseAsync(this.Chat, Prompts.AnswerTemplate, arguments).ConfigureAwait(false);
        //await this.PublishMessageAsync(response.ToResult(), new(Topics.UserProxyTopic)).ConfigureAwait(false); // %%% TOPIC: IS PROPER ???
    }

    private async Task<ChatMessageContent> GetMessageAsync(IPromptTemplate template, KernelArguments arguments)
    {
        string input = await template.RenderAsync(this._kernel, arguments).ConfigureAwait(false);
        return new ChatMessageContent(AuthorRole.User, input);
    }

    private async Task<ChatMessageContent> GetResponseAsync(
        ChatHistory internalChat,
        IPromptTemplate template,
        KernelArguments arguments,
        PromptExecutionSettings? executionSettings = null)
    {
        ChatMessageContent message = await this.GetMessageAsync(template, arguments).ConfigureAwait(false);
        internalChat.Add(message);
        IChatCompletionService chatService = this._kernel.GetRequiredService<IChatCompletionService>(this.Settings.ServiceId);
        ChatMessageContent response = await chatService.GetChatMessageContentAsync(internalChat, executionSettings).ConfigureAwait(false);
        internalChat.Add(response);
        return response;
    }
}
