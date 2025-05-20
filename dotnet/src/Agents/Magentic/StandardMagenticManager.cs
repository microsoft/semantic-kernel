// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Magentic.Internal;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// A <see cref="MagenticManager"/> that provides orchestration logic for managing magentic agents,
/// including preparing facts, plans, ledgers, evaluating progress, and generating a final answer.
/// </summary>
public sealed class StandardMagenticManager : MagenticManager
{
    private static readonly Kernel EmptyKernel = new();

    private readonly IChatCompletionService _service;
    private readonly PromptExecutionSettings _executionSettings;

    private string _facts = string.Empty;
    private string _plan = string.Empty;

    /// <summary>
    /// Initializes a new instance of the <see cref="StandardMagenticManager"/> class.
    /// </summary>
    /// <param name="service">The chat completion service to use for generating responses.</param>
    /// <param name="executionSettings">The prompt execution settings to use for the chat completion service.</param>
    public StandardMagenticManager(IChatCompletionService service, PromptExecutionSettings executionSettings)
    {
        Verify.NotNull(service, nameof(service));
        Verify.NotNull(executionSettings, nameof(executionSettings));

        if (!executionSettings.SupportsResponseFormat())
        {
            throw new KernelException($"Unable to proceed with {nameof(PromptExecutionSettings)} that does not support structured JSON output.");
        }

        if (executionSettings.IsFrozen)
        {
            throw new KernelException($"Unable to proceed with frozen {nameof(PromptExecutionSettings)}.");
        }

        this._service = service;
        this._executionSettings = executionSettings;
        this._executionSettings.SetResponseFormat<MagenticProgressLedger>();
    }

    /// <inheritdoc/>
    public override async ValueTask<IList<ChatMessageContent>> PlanAsync(MagenticManagerContext context, CancellationToken cancellationToken)
    {
        this._facts = await this.PrepareTaskFactsAsync(context, MagenticPrompts.NewFactsTemplate, cancellationToken).ConfigureAwait(false);
        this._plan = await this.PrepareTaskPlanAsync(context, MagenticPrompts.NewPlanTemplate, cancellationToken).ConfigureAwait(false);

        Debug.WriteLine($"\n<FACTS>:\n{this._facts}\n</FACTS>\n\n<PLAN>:\n{this._plan}\n</PLAN>\n");

        return await this.PrepareTaskLedgerAsync(context, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async ValueTask<IList<ChatMessageContent>> ReplanAsync(MagenticManagerContext context, CancellationToken cancellationToken)
    {
        this._facts = await this.PrepareTaskFactsAsync(context, MagenticPrompts.RefreshFactsTemplate, cancellationToken).ConfigureAwait(false);
        this._plan = await this.PrepareTaskPlanAsync(context, MagenticPrompts.RefreshPlanTemplate, cancellationToken).ConfigureAwait(false);

        Debug.WriteLine($"\n<FACTS>:\n{this._facts}\n</FACTS>\n\n<PLAN>:\n{this._plan}\n</PLAN>\n");

        return await this.PrepareTaskLedgerAsync(context, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async ValueTask<MagenticProgressLedger> EvaluateTaskProgressAsync(MagenticManagerContext context, CancellationToken cancellationToken = default)
    {
        ChatHistory internalChat = [.. context.History];
        KernelArguments arguments =
            new()
            {
                { MagenticPrompts.Parameters.Task, this.FormatInputTask(context.Task) },
                { MagenticPrompts.Parameters.Team, context.Team.FormatNames() },
            };
        string response = await this.GetResponseAsync(internalChat, MagenticPrompts.StatusTemplate, arguments, this._executionSettings, cancellationToken).ConfigureAwait(false);
        MagenticProgressLedger status =
            JsonSerializer.Deserialize<MagenticProgressLedger>(response) ??
            throw new InvalidDataException($"Message content does not align with requested type: {nameof(MagenticProgressLedger)}.");

        return status;
    }

    /// <inheritdoc/>
    public override async ValueTask<ChatMessageContent> PrepareFinalAnswerAsync(MagenticManagerContext context, CancellationToken cancellationToken = default)
    {
        KernelArguments arguments =
            new()
            {
                { MagenticPrompts.Parameters.Task, context.Task },
            };
        string response = await this.GetResponseAsync(context.History, MagenticPrompts.AnswerTemplate, arguments, executionSettings: null, cancellationToken).ConfigureAwait(false);

        return new ChatMessageContent(AuthorRole.Assistant, response);
    }

    private async ValueTask<string> PrepareTaskFactsAsync(MagenticManagerContext context, IPromptTemplate promptTemplate, CancellationToken cancellationToken = default)
    {
        KernelArguments arguments =
            new()
            {
                { MagenticPrompts.Parameters.Task, this.FormatInputTask(context.Task) },
                { MagenticPrompts.Parameters.Facts, this._facts },
            };
        return
            await this.GetResponseAsync(
                context.History,
                promptTemplate,
                arguments,
                executionSettings: null,
                cancellationToken).ConfigureAwait(false);
    }

    private async ValueTask<string> PrepareTaskPlanAsync(MagenticManagerContext context, IPromptTemplate promptTemplate, CancellationToken cancellationToken = default)
    {
        KernelArguments arguments =
            new()
            {
                { MagenticPrompts.Parameters.Team, context.Team.FormatList() },
            };

        return
            await this.GetResponseAsync(
                context.History,
                promptTemplate,
                arguments,
                executionSettings: null,
                cancellationToken).ConfigureAwait(false);
    }

    private async ValueTask<IList<ChatMessageContent>> PrepareTaskLedgerAsync(MagenticManagerContext context, CancellationToken cancellationToken = default)
    {
        KernelArguments arguments =
            new()
            {
                { MagenticPrompts.Parameters.Task, this.FormatInputTask(context.Task) },
                { MagenticPrompts.Parameters.Team, context.Team.FormatList() },
                { MagenticPrompts.Parameters.Facts, this._facts },
                { MagenticPrompts.Parameters.Plan, this._plan },
            };
        string ledger = await this.GetMessageAsync(MagenticPrompts.LedgerTemplate, arguments).ConfigureAwait(false);

        return [new ChatMessageContent(AuthorRole.System, ledger)];
    }

    private async ValueTask<string> GetMessageAsync(IPromptTemplate template, KernelArguments arguments)
    {
        return await template.RenderAsync(EmptyKernel, arguments).ConfigureAwait(false);
    }

    private async Task<string> GetResponseAsync(
        IReadOnlyList<ChatMessageContent> internalChat,
        IPromptTemplate template,
        KernelArguments arguments,
        PromptExecutionSettings? executionSettings,
        CancellationToken cancellationToken = default)
    {
        ChatHistory history = [.. internalChat];
        string message = await this.GetMessageAsync(template, arguments).ConfigureAwait(false);
        history.Add(new ChatMessageContent(AuthorRole.User, message));
        ChatMessageContent response = await this._service.GetChatMessageContentAsync(history, executionSettings, kernel: null, cancellationToken).ConfigureAwait(false);
        return response.Content ?? string.Empty;
    }

    private string FormatInputTask(IReadOnlyList<ChatMessageContent> inputTask) => string.Join("\n", inputTask.Select(m => $"{m.Content}"));
}
