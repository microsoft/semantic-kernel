// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// %%% COMMENT
/// </summary>
/// <param name="kernel"></param>
/// <param name="context"></param>
public delegate Task StepFunction(Kernel kernel, KernelProcessStepContext context);

/// <summary>
/// Step in a process that represents an ObjectModel.
/// </summary>
public class KernelDelegateProcessStep : KernelProcessStep
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public const string FunctionName = "Invoke";

    private readonly StepFunction _stepFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelDelegateProcessStep"/> class with the specified step function.
    /// </summary>
    /// <param name="stepFunction"></param>
    /// <exception cref="ArgumentNullException"></exception>
    public KernelDelegateProcessStep(StepFunction stepFunction)
    {
        this._stepFunction = stepFunction ?? throw new ArgumentNullException(nameof(stepFunction));
    }

    /// <summary>
    /// Invokes the step function with the provided kernel and context.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="context"></param>
    /// <returns></returns>
    [KernelFunction(FunctionName)]
    public Task InvokeAsync(Kernel kernel, KernelProcessStepContext context) => this._stepFunction(kernel, context);
}
