// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Abstractions;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.ChatCompletion;
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
        IChatCompletionService chatCompletion = context.Kernel.Services.GetRequiredService<IChatCompletionService>();
        EvaluationResult<string> result = context.ExpressionEngine.GetValue(this.Model.UserInput!, context.Scopes); // %%% FAILURE CASE (CATCH) & NULL OVERRIDE

        ChatHistory history = [];
        if (this.Model.AdditionalInstructions is not null)
        {
            string? instructions = context.Engine.Format(this.Model.AdditionalInstructions);
            if (!string.IsNullOrWhiteSpace(instructions))
            {
                history.AddSystemMessage(instructions);
            }
        }
        history.AddUserMessage(result.Value);
        ChatMessageContent response = await chatCompletion.GetChatMessageContentAsync(history, cancellationToken: cancellationToken).ConfigureAwait(false);
        StringValue responseValue = FormulaValue.New(response.ToString());

        this.AssignTarget(context, responseValue);
    }
}
