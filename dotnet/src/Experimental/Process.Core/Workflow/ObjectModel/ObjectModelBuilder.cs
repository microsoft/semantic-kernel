// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Yaml;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder for converting a Foundry workflow object-model YAML definition into a process.
/// </summary>
public static class ObjectModelBuilder
{
    /// <summary>
    /// Builds a process from the provided YAML definition of a CPS Topic ObjectModel.
    /// </summary>
    /// <param name="yamlReader">The reader that provides the workflow object model YAML.</param>
    /// <param name="messageId">The identifier for the message.</param>
    /// <param name="context">The hosting context for the workflow.</param>
    /// <returns>The <see cref="KernelProcess"/> that corresponds with the YAML object model.</returns>
    public static KernelProcess Build(TextReader yamlReader, string messageId, WorkflowContext? context = null)
    {
        Console.WriteLine("@ PARSING YAML");
        BotElement rootElement = YamlSerializer.Deserialize<BotElement>(yamlReader) ?? throw new KernelException("Unable to parse YAML content.");
        string rootId = GetRootId(rootElement);

        Console.WriteLine("@ INITIALIZING BUILDER");
        ProcessActionScopes scopes = new();
        ProcessBuilder processBuilder = new(rootId);
        ProcessStepBuilder initStep = processBuilder.AddStepFromType<RootWorkflowStep, ProcessActionScopes>(scopes, rootId);
        processBuilder.OnInputEvent(messageId).SendEventTo(new ProcessFunctionTargetBuilder(initStep));

        Console.WriteLine("@ INTERPRETING MODEL");
        ProcessActionVisitor visitor = new(processBuilder, context ?? new WorkflowContext(), scopes);
        ProcessActionWalker walker = new(rootElement, visitor);

        Console.WriteLine("@ FINALIZING PROCESS");
        ProcessStepBuilder errorHandler = // %%% DYNAMIC/CONTEXT ???
            processBuilder.AddStepFromFunction(
                $"{processBuilder.Name}_unhandled_error",
                (kernel, context) =>
                {
                    // Handle unhandled errors here
                    Console.WriteLine("*** PROCESS ERROR - Unhandled error"); // %%% EXTERNAL
                    return Task.CompletedTask;
                });
        processBuilder.OnError().SendEventTo(new ProcessFunctionTargetBuilder(errorHandler));

        Console.WriteLine("@ PROCESS DEFINED");
        return processBuilder.Build();
    }

    private static string GetRootId(BotElement element) =>
        element switch
        {
            AdaptiveDialog adaptiveDialog => adaptiveDialog.BeginDialog?.Id.Value ?? throw new InvalidOperationException("Undefined dialog"), // %%% EXCEPTION TYPE
            _ => throw new KernelException($"Unsupported root element: {element.GetType().Name}."), // %%% EXCEPTION TYPE
        };

    private sealed class RootWorkflowStep : KernelProcessStep<ProcessActionScopes>
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
        public void InitializeProcess(string? message)
        {
            if (this._scopes == null)
            {
                throw new KernelException("Scopes have not been initialized. Ensure that the step is activated before calling this function.");
            }

            Console.WriteLine("!!! INIT WORKFLOW"); // %%% REMOVE
            this._scopes.Set("LastMessage", ActionScopeType.System, StringValue.New(message)); // %%% MAGIC CONST "LastMessage"
        }
    }
}
