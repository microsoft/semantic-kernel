// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class AnswerQuestionWithAIAction : AssignmentAction<AnswerQuestionWithAI>
{
    public AnswerQuestionWithAIAction(AnswerQuestionWithAI action)
        : base(action, () => action.Variable?.Path)
    {
        if (string.IsNullOrWhiteSpace(action.UserInput?.ExpressionText))
        {
            throw new InvalidActionException($"{nameof(AnswerQuestionWithAI)} must define {nameof(AnswerQuestionWithAI.UserInput)}");
        }
    }

    public override async Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        IChatCompletionService chatCompletion = kernel.Services.GetRequiredService<IChatCompletionService>();
        FormulaValue expressionResult = engine.Eval(this.Action.UserInput!.ExpressionText);
        if (expressionResult is not StringValue stringResult)
        {
            throw new InvalidActionException($"{nameof(AnswerQuestionWithAI)} requires text for {nameof(AnswerQuestionWithAI.UserInput)}");
        }

        ChatHistory history = [];
        if (this.Action.AdditionalInstructions is not null)
        {
            string? instructions = engine.Format(this.Action.AdditionalInstructions);
            if (!string.IsNullOrWhiteSpace(instructions))
            {
                history.AddSystemMessage(instructions);
            }
        }
        history.AddUserMessage(stringResult.Value);
        ChatMessageContent response = await chatCompletion.GetChatMessageContentAsync(history, cancellationToken: cancellationToken).ConfigureAwait(false);
        StringValue responseValue = FormulaValue.New(response.ToString());

        this.AssignTarget(engine, scopes, responseValue);
    }
}
