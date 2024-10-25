// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Process.Runtime;

internal static class StepExtensions
{
    /// <summary>
    /// The generic state type for a process step.
    /// </summary>
    private static readonly Type s_genericType = typeof(KernelProcessStep<>);

    public static KernelProcessStepInfo Clone(this KernelProcessStepInfo step, ILogger logger)
    {
        if (step is KernelProcess subProcess)
        {
            return subProcess.CloneProcess(logger);
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
        KernelProcessStepState? newState = (KernelProcessStepState?)Activator.CreateInstance(stateType, sourceState.Name, sourceState.Id);
        if (newState == null)
        {
            string errorMessage = $"Failed to instantiate state: {stateType.Name} [{sourceState.Id}].";
            logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
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
                string errorMessage = "The generic type argument for the KernelProcessStep subclass could not be determined.";
                logger?.LogError("{ErrorMessage}", errorMessage);
                throw new KernelException(errorMessage);
            }

            stateType = typeof(KernelProcessStepState<>).MakeGenericType(userStateType);
            if (stateType is null)
            {
                string errorMessage = "The generic type argument for the KernelProcessStep subclass could not be determined.";
                logger?.LogError("{ErrorMessage}", errorMessage);
                throw new KernelException(errorMessage);
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
    /// <returns><see cref="Dictionary{TKey, TValue}"/></returns>
    /// <exception cref="InvalidOperationException"></exception>
    public static Dictionary<string, Dictionary<string, object?>?> FindInputChannels(this IKernelProcessMessageChannel channel, Dictionary<string, KernelFunction> functions, ILogger? logger)
    {
        if (functions is null)
        {
            string errorMessage = "Internal Error: The step has not been initialized.";
            logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
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
                else
                {
                    inputs[kvp.Key]![param.Name] = null;
                }
            }
        }

        return inputs;
    }

    /// <summary>
    /// Attempts to find an instance of <![CDATA['KernelProcessStep<>']]> within the provided types hierarchy.
    /// </summary>
    /// <param name="type">The type to examine.</param>
    /// <param name="genericStateType">The matching type if found, otherwise null.</param>
    /// <returns>True if a match is found, false otherwise.</returns>
    /// TODO: Move this to a share process utilities project.
    private static bool TryGetSubtypeOfStatefulStep(this Type? type, out Type? genericStateType)
    {
        while (type != null && type != typeof(object))
        {
            if (type.IsGenericType && type.GetGenericTypeDefinition() == s_genericType)
            {
                genericStateType = type;
                return true;
            }

            type = type.BaseType;
        }

        genericStateType = null;

        return false;
    }
}
