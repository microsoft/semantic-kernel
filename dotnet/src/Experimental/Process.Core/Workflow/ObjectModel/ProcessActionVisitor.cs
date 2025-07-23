// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal sealed class ProcessActionVisitor : DialogActionVisitor
{
    private readonly ProcessBuilder _processBuilder;
    private readonly ProcessStepBuilder _unhandledErrorStep;
    private readonly HostContext _context;
    private readonly ProcessActionScopes _scopes;
    private readonly Dictionary<ActionId, ProcessStepBuilder> _steps;
    private readonly Stack<ProcessActionVisitorContext> _contextStack;
    private readonly List<(ActionId TargetId, ProcessStepEdgeBuilder SourceEdge)> _linkCache;

    public ProcessActionVisitor(
        ProcessBuilder processBuilder,
        HostContext context,
        ProcessStepBuilder sourceStep,
        ProcessActionScopes scopes)
    {
        ProcessActionVisitorContext rootContext = new(sourceStep);
        this._contextStack = [];
        this._contextStack.Push(rootContext);
        this._steps = [];
        this._linkCache = [];
        this._processBuilder = processBuilder;
        this._context = context;
        this._scopes = scopes;
        this._unhandledErrorStep =
            processBuilder.AddStepFromFunction(
                $"{processBuilder.Name}_unhandled_error",
                (kernel, context) =>
                {
                    // Handle unhandled errors here
                    Console.WriteLine("*** PROCESS ERROR - Unhandled error"); // %%% DEVTRACE
                    return Task.CompletedTask;
                });
    }

    public void Complete()
    {
        // Close the current context
        this.CurrentContext.Then().StopProcess();

        // Process the cached links
        foreach ((ActionId targetId, ProcessStepEdgeBuilder sourceEdge) in this._linkCache)
        {
            // Link the queued context to the step
            ProcessStepBuilder step = this._steps[targetId]; // %%% TRY
            Console.WriteLine($"> CONNECTING {sourceEdge.Source.Id} => {targetId}");
            sourceEdge.SendEventTo(new ProcessFunctionTargetBuilder(step));
        }
        this._linkCache.Clear();

        // Visitor is complete, all actions have been processed
        Console.WriteLine("> COMPLETE"); // %%% DEVTRACE
    }

    private ProcessActionVisitorContext CurrentContext => this._contextStack.Peek();

    protected override void Visit(ActionScope item)
    {
        this.Trace(item, isSkipped: false);

        this.AddContainer(item.Id.Value);
    }

    protected override void Visit(ConditionGroup item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new ConditionGroupAction(item));

        // Visit each action in the condition group
        int index = 1;
        foreach (ConditionItem conditionItem in item.Conditions)
        {
            ProcessStepBuilder step = this.CreateContainerStep(this.CurrentContext, conditionItem.Id ?? $"{item.Id.Value}_item{index}");
            this._contextStack.Push(new ProcessActionVisitorContext(step));

            conditionItem.Accept(this);

            ProcessActionVisitorContext conditionContext = this._contextStack.Pop();
            KernelProcessEdgeCondition? condition = null;

            if (conditionItem.Condition is not null)
            {
                // %%% VERIFY IF ONLY ONE CONDITION IS EXPECTED / ALLOWED
                condition =
                    new((stepEvent, state) =>
                    {
                        RecalcEngine engine = this.CreateEngine();
                        bool result = engine.Eval(conditionItem.Condition.ExpressionText ?? "true").AsBoolean();
                        Console.WriteLine($"!!! CONDITION: {conditionItem.Condition.ExpressionText ?? "true"}={result}");
                        return Task.FromResult(result);
                    });
            }

            this.CurrentContext.Then(conditionContext.Step, condition);

            ++index;
        }
    }

    protected override void Visit(GotoAction item)
    {
        this.Trace(item, isSkipped: false);

        this.AddContainer(item.Id.Value);
        // Store the link for processing after all actions have steps.
        this._linkCache.Add((item.ActionId, this.CurrentContext.Then())); // %%% DRY
        // Create an orphaned context for continuity
        this.AddDead(item.Id.Value);
    }

    protected override void Visit(Foreach item)
    {
        this.Trace(item);

        this.AddAction(new ForeachAction(item));
    }

    protected override void Visit(BreakLoop item)
    {
        this.Trace(item);
    }

    protected override void Visit(ContinueLoop item)
    {
        this.Trace(item);
    }

    protected override void Visit(EndConversation item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new EndConversationAction(item));
        // Stop the process, this is a terminal action
        this.CurrentContext.Then().StopProcess();
        // Create an orphaned context for continuity
        this.AddDead(item.Id.Value);
    }

    protected override void Visit(AnswerQuestionWithAI item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new AnswerQuestionWithAIAction(item));
    }

    protected override void Visit(SetVariable item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new SetVariableAction(item));
    }

    protected override void Visit(SetTextVariable item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new SetTextVariableAction(item));
    }

    protected override void Visit(ClearAllVariables item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new ClearAllVariablesAction(item));
    }

    protected override void Visit(ResetVariable item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new ResetVariableAction(item));
    }

    protected override void Visit(EditTable item)
    {
        this.Trace(item);
    }

    protected override void Visit(EditTableV2 item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new EditTableV2Action(item));
    }

    protected override void Visit(ParseValue item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new ParseValueAction(item));
    }

    protected override void Visit(SendActivity item)
    {
        this.Trace(item, isSkipped: false);

        this.AddAction(new SendActivityAction(item, this._context.ActivityNotificationHandler));
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

        this.AddAction(new BeginDialogAction(item));
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

    private void AddAction(ProcessAction? action)
    {
        if (action is not null)
        {
            // Add the action to the existing context
            this.AddStep(this.CreateActionStep(this.CurrentContext, action));
        }
    }

    private void AddContainer(string contextId)
    {
        this.AddStep(this.CreateContainerStep(this.CurrentContext, contextId));
    }

    private void AddDead(string contextId)
    {
        this.CurrentContext.Step = this.CreateContainerStep(this.CurrentContext, $"dead_{contextId}");
    }

    private void AddStep(ProcessStepBuilder step)
    {
        this._steps[step.Id] = step;
        this.ContinueWith(step);
    }

    private ProcessStepBuilder CreateContainerStep(ProcessActionVisitorContext currentContext, string contextId)
    {
        return this.InitializeStep(
            this._processBuilder.AddStepFromFunction(
                contextId,
                (kernel, context) =>
                {
                    Console.WriteLine($"!!! STEP [{contextId}]"); // %%% DEVTRACE
                    return Task.CompletedTask;
                }));
    }

    // This implementation accepts the context as a parameter in order to pin the context closure.
    // The step cannot reference this.CurrentContext directly, as this will always be the final context.
    private ProcessStepBuilder CreateActionStep(ProcessActionVisitorContext currentContext, ProcessAction action)
    {
        return this.InitializeStep(
            this._processBuilder.AddStepFromFunction(
                action.Id,
                async (kernel, context) =>
                {
                    Console.WriteLine($"!!! STEP {action.GetType().Name} [{action.Id}]"); // %%% DEVTRACE

                    if (action.Model.Disabled) // %%% VALIDATE
                    {
                        Console.WriteLine($"!!! DISABLED {action.GetType().Name} [{action.Id}]"); // %%% DEVTRACE
                        return;
                    }

                    try
                    {
                        ProcessActionContext actionContext = new(this.CreateEngine(), this._scopes, kernel);
                        await action.ExecuteAsync(actionContext, cancellationToken: default).ConfigureAwait(false); // %%% CANCEL TOKEN
                    }
                    catch (ProcessActionException)
                    {
                        Console.WriteLine($"*** STEP [{action.Id}] ERROR - Action failure"); // %%% DEVTRACE
                        throw;
                    }
                    catch (Exception exception)
                    {
                        Console.WriteLine($"*** STEP [{action.Id}] ERROR - {exception.GetType().Name}\n{exception.Message}"); // %%% DEVTRACE
                        throw;
                    }
                }));
    }

    private ProcessStepBuilder InitializeStep(ProcessStepBuilder step)
    {
        // Capture unhandled errors for the given step
        step.OnFunctionError(KernelDelegateProcessStep.FunctionName).SendEventTo(new ProcessFunctionTargetBuilder(this._unhandledErrorStep));

        return step;
    }

    private void ContinueWith(ProcessStepBuilder newStep, KernelProcessEdgeCondition? condition = null)
    {
        this.CurrentContext.Then(newStep, condition);
        this.CurrentContext.Step = newStep;
    }

    private RecalcEngine CreateEngine() => RecalcEngineFactory.Create(this._scopes, this._context.MaximumExpressionLength);

    private void Trace(DialogAction item, bool isSkipped = true)
    {
        //Console.WriteLine($"> {(isSkipped ? "EMPTY" : "VISIT")}{new string('\t', this._contextStack.Count - 1)} - {this.Format(item)} => {this.Format(item.Parent)}"); // %%% DEVTRACE
        Console.WriteLine($"> {(isSkipped ? "EMPTY" : "VISIT")} x{this._contextStack.Count} - {this.Format(item)} => {this.Format(item.Parent)}"); // %%% DEVTRACE
    }

    private string Format(DialogAction action) => $"{action.GetType().Name} [{action.Id.Value}]";

    private string Format(BotElement? element) =>
        element switch
        {
            null => "(root)",
            DialogAction action => this.Format(action),
            ConditionItem conditionItem => $"{conditionItem.GetType().Name} [{conditionItem.Id}]",
            OnActivity activity => $"{activity.GetType().Name} (workflow)",
            _ => $"{element.GetType().Name} (unknown element)"
        };
}
