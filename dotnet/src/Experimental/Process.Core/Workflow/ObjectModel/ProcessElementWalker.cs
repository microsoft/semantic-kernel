// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Yaml;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal sealed class ProcessActionWalker : BotElementWalker
{
    private readonly ProcessActionVisitor _visitor;

    public ProcessActionWalker(ProcessBuilder processBuilder, string messageId, ProcessActionEnvironment processEnvironment)
    {
        this._visitor = CreateActionVisitor(processBuilder, messageId, processEnvironment);
    }

    public void ProcessYaml(string yaml)
    {
        Console.WriteLine("### PARSING YAML");
        BotElement root = YamlSerializer.Deserialize<BotElement>(yaml) ?? throw new KernelException("Unable to parse YAML content.");
        Console.WriteLine("### INTERPRETING MODEL");
        this.Visit(root);
        this._visitor.Complete();
        Console.WriteLine("### PROCESS CREATED");
    }

    public override bool DefaultVisit(BotElement definition)
    {
        if (definition is DialogAction action)
        {
            action.Accept(this._visitor);
        }

        return true;
    }

    private static ProcessActionVisitor CreateActionVisitor(ProcessBuilder processBuilder, string messageId, ProcessActionEnvironment processEnvironment)
    {
        ProcessActionScopes scopes = [];

        ProcessStepBuilder initStep = processBuilder.AddStepFromType<InitializeProcessStep, ProcessActionScopes>(scopes, "init");

        processBuilder.OnInputEvent(messageId).SendEventTo(new ProcessFunctionTargetBuilder(initStep));

        return new ProcessActionVisitor(processBuilder, processEnvironment, initStep, scopes);
    }

    private sealed class InitializeProcessStep : KernelProcessStep<ProcessActionScopes>
    {
        private ProcessActionScopes? _scopes;

        public override ValueTask ActivateAsync(KernelProcessStepState<ProcessActionScopes> state)
        {
            this._scopes = state.State;

#if !NETCOREAPP
            return new ValueTask();
#else
            return ValueTask.CompletedTask;
#endif
        }

        [KernelFunction(KernelDelegateProcessStep.FunctionName)]
        [Description("Initialize the process step")]
        public void InitializeProcess(string message)
        {
            if (this._scopes == null)
            {
                throw new KernelException("Scopes have not been initialized. Ensure that the step is activated before calling this function.");
            }

            Console.WriteLine("!!! INIT WORKFLOW");
            FormulaValue inputTask = StringValue.New(message);
            this._scopes[ActionScopeTypes.System]["LastMessage"] = inputTask; // %%% MAGIC CONST
        }
    }
}
