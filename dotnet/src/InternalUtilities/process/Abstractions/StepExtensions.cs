// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Internal;

internal static class StepExtensions
{
    public static KernelProcessStepInfo Clone(this KernelProcessStepInfo step, ILogger logger)
    {
        if (step is KernelProcess subProcess)
        {
            return subProcess.CloneProcess(logger);
        }

        if (step is KernelProcessMap mapStep)
        {
            return mapStep.CloneMap(logger);
        }

        Type stateType = step.InnerStepType.ExtractStateType(out Type? userStateType, logger);

        KernelProcessStepState newState = step.State.Clone(stateType, userStateType, logger);

        KernelProcessStepInfo copy =
            new(
                step.InnerStepType,
                newState,
                step.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList()));

        return copy;
    }

    // Exposed for testing
    public static KernelProcessStepState Clone(this KernelProcessStepState sourceState, Type stateType, Type? userStateType, ILogger logger)
    {
        KernelProcessStepState? newState = (KernelProcessStepState?)Activator.CreateInstance(stateType, sourceState.Name, sourceState.Version, sourceState.Id);
        if (newState == null)
        {
            throw new KernelException($"Failed to instantiate state: {stateType.Name} [{sourceState.Id}].").Log(logger);
        }

        if (userStateType != null)
        {
            newState.InitializeUserState(stateType, userStateType);
        }

        return newState;
    }

    public static Type ExtractStateType(this Type? innerStepType, out Type? userStateType, ILogger? logger)
    {
        Type stateType;

        if (innerStepType.TryGetSubtypeOfStatefulStep(out Type? genericStepType) && genericStepType is not null)
        {
            // The step is a subclass of KernelProcessStep<>, so we need to extract the generic type argument
            // and create an instance of the corresponding KernelProcessStepState<>.
            userStateType = genericStepType.GetGenericArguments()[0];
            if (userStateType is null)
            {
                throw new KernelException("The generic type argument for the KernelProcessStep subclass could not be determined.").Log(logger);
            }

            stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
            if (stateType is null)
            {
                throw new KernelException("The generic type argument for the KernelProcessStep subclass could not be determined.").Log(logger);
            }
        }
        else
        {
            // The step is a KernelProcessStep with no use`-defined state, so we can use the base KernelProcessStepState.
            stateType = typeof(KernelProcessStepState);
            userStateType = null;
        }

        return stateType;
    }

    public static void InitializeUserState(this KernelProcessStepState stateObject, Type stateType, Type? userStateType)
    {
        if (stateType.IsGenericType && userStateType != null)
        {
            var userState = stateType.GetProperty(nameof(KernelProcessStepState<object>.State))?.GetValue(stateObject);
            if (userState is null)
            {
                stateType.GetProperty(nameof(KernelProcessStepState<object>.State))?.SetValue(stateObject, Activator.CreateInstance(userStateType));
            }
        }
    }

    /// <summary>
    /// Examines the KernelFunction for the step and creates a dictionary of input channels.
    /// Some types such as KernelProcessStepContext are special and need to be injected into
    /// the function parameter. Those objects are instantiated at this point.
    /// </summary>
    /// <param name="channel">The source channel to evaluate</param>
    /// <param name="functions">A dictionary of KernelFunction instances.</param>
    /// <param name="logger">An instance of <see cref="ILogger"/>.</param>
    /// <param name="externalMessageChannel">An instance of <see cref="IExternalKernelProcessMessageChannel"/></param>
    /// <returns><see cref="Dictionary{TKey, TValue}"/></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public static Dictionary<string, Dictionary<string, object?>?> FindInputChannels(
        this IKernelProcessMessageChannel channel,
        Dictionary<string, KernelFunction> functions,
        ILogger? logger,
        IExternalKernelProcessMessageChannel? externalMessageChannel = null)
    {
        if (functions is null)
        {
            throw new KernelException("Internal Error: The step has not been initialized.").Log(logger);
        }

        Dictionary<string, Dictionary<string, object?>?> inputs = new();
        foreach (var kvp in functions)
        {
            inputs[kvp.Key] = new();
            foreach (var param in kvp.Value.Metadata.Parameters)
            {
                // Optional parameters are should not be added to the input dictionary.
                if (!param.IsRequired)
                {
                    continue;
                }

                // Parameters of type KernelProcessStepContext are injected by the process
                // and are instantiated here.
                if (param.ParameterType == typeof(KernelProcessStepContext))
                {
                    inputs[kvp.Key]![param.Name] = new KernelProcessStepContext(channel);
                }
                else if (param.ParameterType == typeof(KernelProcessStepExternalContext))
                {
                    inputs[kvp.Key]![param.Name] = new KernelProcessStepExternalContext(externalMessageChannel);
                }
                else
                {
                    inputs[kvp.Key]![param.Name] = null;
                }
            }
        }

        return inputs;
    }
}
