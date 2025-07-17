// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class AnswerQuestionWithAIAction : AssignmentAction<AnswerQuestionWithAI>
{
    public AnswerQuestionWithAIAction(AnswerQuestionWithAI model)
        : base(model, () => model.Variable?.Path)
    {
        if (string.IsNullOrWhiteSpace(model.UserInput?.ExpressionText))
        {
            throw new InvalidActionException($"{nameof(AnswerQuestionWithAI)} must define {nameof(AnswerQuestionWithAI.UserInput)}");
        }
    }

    protected override async Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        IChatCompletionService chatCompletion = context.Kernel.Services.GetRequiredService<IChatCompletionService>();
        FormulaValue expressionResult = context.Engine.Eval(this.Model.UserInput!.ExpressionText);
        if (expressionResult is not StringValue stringResult)
        {
            throw new InvalidActionException($"{nameof(AnswerQuestionWithAI)} requires text for {nameof(AnswerQuestionWithAI.UserInput)}");
        }

        ChatHistory history = [];
        if (this.Model.AdditionalInstructions is not null)
        {
            string? instructions = context.Engine.Format(this.Model.AdditionalInstructions);
            if (!string.IsNullOrWhiteSpace(instructions))
            {
                history.AddSystemMessage(instructions);
            }
        }
        history.AddUserMessage(stringResult.Value);
        ChatMessageContent response = await chatCompletion.GetChatMessageContentAsync(history, cancellationToken: cancellationToken).ConfigureAwait(false);
        StringValue responseValue = FormulaValue.New(response.ToString());

        this.AssignTarget(context, responseValue);
    }
}
