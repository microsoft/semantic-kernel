// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Agents.Persistent;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Abstractions;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class AnswerQuestionWithAIAction : AssignmentAction<AnswerQuestionWithAI>
{
    public AnswerQuestionWithAIAction(AnswerQuestionWithAI model)
        : base(model, Throw.IfNull(model.Variable?.Path, $"{nameof(model)}.{nameof(model.Variable)}.{nameof(InitializablePropertyPath.Path)}"))
    {
    }

    protected override async Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        PersistentAgentsClient client = context.ClientFactory.Invoke();
        PersistentAgent model = await client.Administration.GetAgentAsync("asst_ueIjfGxAjsnZ4A61LlbjG9vJ", cancellationToken).ConfigureAwait(false);
        AzureAIAgent agent = new(model, client);

        string? userInput = null;
        if (this.Model.UserInput is not null)
        {
            EvaluationResult<string> result = context.ExpressionEngine.GetValue(this.Model.UserInput!, context.Scopes); // %%% FAILURE CASE (CATCH) & NULL OVERRIDE
            userInput = result.Value;
        }

        AgentInvokeOptions options =
            new()
            {
                AdditionalInstructions = context.Engine.Format(this.Model.AdditionalInstructions) ?? string.Empty,
            };
        AgentResponseItem<ChatMessageContent> response =
            userInput != null ?
                await agent.InvokeAsync(userInput, thread: null, options, cancellationToken).LastAsync(cancellationToken).ConfigureAwait(false) :
                await agent.InvokeAsync(thread: null, options, cancellationToken).LastAsync(cancellationToken).ConfigureAwait(false);
        StringValue responseValue = FormulaValue.New(response.Message.ToString());

        this.AssignTarget(context, responseValue);
    }
}
