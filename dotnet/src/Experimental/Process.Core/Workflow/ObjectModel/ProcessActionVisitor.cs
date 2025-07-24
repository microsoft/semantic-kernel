// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal sealed class ProcessActionVisitor : DialogActionVisitor
{
    private readonly ProcessBuilder _processBuilder;
    private readonly ProcessWorkflowBuilder _workflowBuilder;
    private readonly ProcessActionStack _actionStack;
    private readonly HostContext _context;
    private readonly ProcessActionScopes _scopes;

    public ProcessActionVisitor(
        ProcessBuilder processBuilder,
        HostContext context,
        ProcessActionScopes scopes)
    {
        this._actionStack = new ProcessActionStack();
        this._workflowBuilder = new ProcessWorkflowBuilder(processBuilder.Steps.Single());
        this._processBuilder = processBuilder;
        this._context = context;
        this._scopes = scopes;
    }

    public void Complete()
    {
        // Process the cached links
        this._workflowBuilder.ConnectNodes();
    }

    protected override void Visit(ActionScope item)
    {
        this.Trace(item, isSkipped: true);

        //string parentId = item.GetParentId();
        //this._workflowBuilder.AddNode(this.CreateEmptyStep(item.Id.Value), parentId);
        //this._workflowBuilder.AddLink(parentId, item.Id.Value);
    }

    protected override void Visit(ConditionGroup item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new ConditionGroupAction(item));

        // %%% SUPPORT: item.ElseActions

        int index = 1;
        foreach (ConditionItem conditionItem in item.Conditions)
        {
            //KernelProcessEdgeCondition? condition = null;

            //if (conditionItem.Condition is not null)
            //{
            //    // %%% VERIFY IF ONLY ONE CONDITION IS EXPECTED / ALLOWED
            //    condition =
            //        new((stepEvent, state) =>
            //        {
            //            RecalcEngine engine = this.CreateEngine();
            //            bool result = engine.Eval(conditionItem.Condition.ExpressionText ?? "true").AsBoolean();
            //            Console.WriteLine($"!!! CONDITION: {conditionItem.Condition.ExpressionText ?? "true"}={result}");
            //            return Task.FromResult(result);
            //        });
            //}

            ////this.AddScope(conditionItem.Id ?? $"{item.Id.Value}_item{index}", condition);

            //// Visit each action in the condition item
            //conditionItem.Accept(this);

            ////this._workflowBuilder.RemoveScope();

            ++index;
        }
    }

    public override void VisitConditionItem(ConditionItem item)
    {
        Console.WriteLine($"###### ITEM {item.Id}");
        base.VisitConditionItem(item); // %%%
    }

    protected override void Visit(GotoAction item)
    {
        this.Trace(item, isSkipped: false);

        string parentId = item.GetParentId();
        this.ContinueWith(this.CreateStep(item.Id.Value), parentId);
        this._workflowBuilder.AddLink(item.Id.Value, item.ActionId.Value);
        this.RestartFrom(item.Id.Value, parentId);
    }

    protected override void Visit(Foreach item)
    {
        this.Trace(item, isSkipped: false);

        ForeachAction action = new(item);
        this.ContinueWith(action);
        string restartId = this.RestartFrom(action);
        string loopId = $"next_{action.Id}";
        this.ContinueWith(this.CreateStep(loopId, action.TakeNext), action.Id, callback: CompletionHandler);
        this._workflowBuilder.AddLink(loopId, restartId, () => !action.HasValue);
        this.ContinueWith(this.CreateStep($"start_{action.Id}"), action.Id, () => action.HasValue);
        void CompletionHandler(string scopeId)
        {
            string completionId = $"end_{action.Id}";
            this.ContinueWith(this.CreateStep(completionId), action.Id);
            this._workflowBuilder.AddLink(completionId, loopId);
        }
    }

    protected override void Visit(BreakLoop item) // %%% SUPPORT
    {
        this.Trace(item);
    }

    protected override void Visit(ContinueLoop item) // %%% SUPPORT
    {
        this.Trace(item);
    }

    protected override void Visit(EndConversation item)
    {
        this.Trace(item, isSkipped: false);

        EndConversationAction action = new(item);
        this.ContinueWith(action);
        this.RestartFrom(action);
    }

    protected override void Visit(AnswerQuestionWithAI item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new AnswerQuestionWithAIAction(item));
    }

    protected override void Visit(SetVariable item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new SetVariableAction(item));
    }

    protected override void Visit(SetTextVariable item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new SetTextVariableAction(item));
    }

    protected override void Visit(ClearAllVariables item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new ClearAllVariablesAction(item));
    }

    protected override void Visit(ResetVariable item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new ResetVariableAction(item));
    }

    protected override void Visit(EditTable item)
    {
        this.Trace(item);
    }

    protected override void Visit(EditTableV2 item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new EditTableV2Action(item));
    }

    protected override void Visit(ParseValue item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new ParseValueAction(item));
    }

    protected override void Visit(SendActivity item)
    {
        this.Trace(item, isSkipped: false);

        this.ContinueWith(new SendActivityAction(item, this._context.ActivityChannel));
    }

    #region Not implemented

    protected override void Visit(DeleteActivity item)
    {
        this.Trace(item);
    }

    protected override void Visit(GetActivityMembers item)
    {
        this.Trace(item);
    }

    protected override void Visit(UpdateActivity item)
    {
        this.Trace(item);
    }

    protected override void Visit(ActivateExternalTrigger item)
    {
        this.Trace(item);
    }

    protected override void Visit(DisableTrigger item)
    {
        this.Trace(item);
    }

    protected override void Visit(WaitForConnectorTrigger item)
    {
        this.Trace(item);
    }

    protected override void Visit(InvokeConnectorAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(InvokeCustomModelAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(InvokeFlowAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(InvokeAIBuilderModelAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(InvokeSkillAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(AdaptiveCardPrompt item)
    {
        this.Trace(item);
    }

    protected override void Visit(Question item)
    {
        this.Trace(item);
    }

    protected override void Visit(CSATQuestion item)
    {
        this.Trace(item);
    }

    protected override void Visit(OAuthInput item)
    {
        this.Trace(item);
    }

    protected override void Visit(BeginDialog item)
    {
        this.Trace(item);
    }

    protected override void Visit(UnknownDialogAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(EndDialog item)
    {
        this.Trace(item);
    }

    protected override void Visit(RepeatDialog item)
    {
        this.Trace(item);
    }

    protected override void Visit(ReplaceDialog item)
    {
        this.Trace(item);
    }

    protected override void Visit(CancelAllDialogs item)
    {
        this.Trace(item);
    }

    protected override void Visit(CancelDialog item)
    {
        this.Trace(item);
    }

    protected override void Visit(EmitEvent item)
    {
        this.Trace(item);
    }

    protected override void Visit(GetConversationMembers item)
    {
        this.Trace(item);
    }

    protected override void Visit(HttpRequestAction item)
    {
        this.Trace(item);
    }

    protected override void Visit(RecognizeIntent item)
    {
        this.Trace(item);
    }

    protected override void Visit(TransferConversation item)
    {
        this.Trace(item);
    }

    protected override void Visit(TransferConversationV2 item)
    {
        this.Trace(item);
    }

    protected override void Visit(SignOutUser item)
    {
        this.Trace(item);
    }

    protected override void Visit(LogCustomTelemetryEvent item)
    {
        this.Trace(item);
    }

    protected override void Visit(DisconnectedNodeContainer item)
    {
        this.Trace(item);
    }

    protected override void Visit(CreateSearchQuery item)
    {
        this.Trace(item);
    }

    protected override void Visit(SearchKnowledgeSources item)
    {
        this.Trace(item);
    }

    protected override void Visit(SearchAndSummarizeWithCustomModel item)
    {
        this.Trace(item);
    }

    protected override void Visit(SearchAndSummarizeContent item)
    {
        this.Trace(item);
    }

    #endregion

    private void ContinueWith(
        ProcessAction action,
        Func<bool>? condition = null,
        ScopeCompletionAction? callback = null) =>
        this.ContinueWith(this.CreateActionStep(action), action.ParentId, condition, callback);

    private void ContinueWith(
        ProcessStepBuilder step,
        string parentId,
        Func<bool>? condition = null,
        ScopeCompletionAction? callback = null)
    {
        this._actionStack.Recognize(parentId, callback);
        this._workflowBuilder.AddNode(step, parentId);
        this._workflowBuilder.AddLinkFromPeer(parentId, step.Id, condition);
    }

    private string RestartFrom(ProcessAction action) =>
        this.RestartFrom(action.Id, action.ParentId);

    private string RestartFrom(string actionId, string parentId)
    {
        string restartId = $"post_{actionId}";
        this._workflowBuilder.AddNode(this.CreateStep(restartId), parentId);
        return restartId;
    }

    private ProcessStepBuilder CreateStep(string actionId, Action<ProcessActionContext>? stepAction = null)
    {
        return
            this._processBuilder.AddStepFromFunction(
                actionId,
                (kernel, context) =>
                {
                    Console.WriteLine($"!!! STEP CUSTOM [{actionId}]"); // %%% REMOVE
                    stepAction?.Invoke(this.CreateActionContext(actionId, kernel));
                    return Task.CompletedTask;
                });
    }

    // This implementation accepts the context as a parameter in order to pin the context closure.
    // The step cannot reference this.CurrentContext directly, as this will always be the final context.
    private ProcessStepBuilder CreateActionStep(ProcessAction action)
    {
        return
            this._processBuilder.AddStepFromFunction(
                action.Id,
                async (kernel, context) =>
                {
                    Console.WriteLine($"!!! STEP {action.GetType().Name} [{action.Id}]"); // %%% REMOVE

                    if (action.Model.Disabled) // %%% VALIDATE
                    {
                        Console.WriteLine($"!!! DISABLED {action.GetType().Name} [{action.Id}]"); // %%% REMOVE
                        return;
                    }

                    try
                    {
                        await action.ExecuteAsync(
                            this.CreateActionContext(action.Id, kernel),
                            cancellationToken: default).ConfigureAwait(false); // %%% CANCELTOKEN
                    }
                    catch (ProcessActionException)
                    {
                        Console.WriteLine($"*** STEP [{action.Id}] ERROR - Action failure"); // %%% LOGGER
                        throw;
                    }
                    catch (Exception exception)
                    {
                        Console.WriteLine($"*** STEP [{action.Id}] ERROR - {exception.GetType().Name}\n{exception.Message}"); // %%% LOGGER
                        throw;
                    }
                });
    }

    private ProcessActionContext CreateActionContext(string actionId, Kernel kernel) => new(this.CreateEngine(), this._scopes, kernel, kernel.LoggerFactory.CreateLogger(actionId));

    private RecalcEngine CreateEngine() => RecalcEngineFactory.Create(this._scopes, this._context.MaximumExpressionLength);

    private void Trace(DialogAction item, bool isSkipped = true)
    {
        Console.WriteLine($"> {(isSkipped ? "EMPTY" : "VISIT")}: {new string('\t', this._workflowBuilder.GetDepth(item.GetParentId()))}{FormatItem(item)} => {FormatParent(item)}"); // %%% LOGGER
    }

    private static string FormatItem(BotElement element) => $"{element.GetType().Name} ({element.GetId()})";

    private static string FormatParent(BotElement element) =>
        element.Parent is null ?
        throw new InvalidActionException($"Undefined parent for {element.GetType().Name} that is member of {element.GetId()}.") :
        $"{element.Parent.GetType().Name} ({element.GetParentId()})";
}
