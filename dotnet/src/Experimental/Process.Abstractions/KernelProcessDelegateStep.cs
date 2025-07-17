// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Signature for a step function targeted by <see cref="KernelDelegateProcessStep"/>.
/// </summary>
/// <param name="kernel">The kernel instance used for processing.</param>
/// <param name="context">The context for the step execution.</param>
public delegate Task StepFunction(Kernel kernel, KernelProcessStepContext context);

/// <summary>
/// Step in a process that represents an ObjectModel.
/// </summary>
public class KernelDelegateProcessStep : KernelProcessStep
{
    /// <summary>
    /// The name assigned to the delegate function that will be invoked by the step.
    /// </summary>
    public const string FunctionName = "Invoke";

    private readonly StepFunction _stepFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelDelegateProcessStep"/> class with the specified step function.
    /// </summary>
    /// <param name="stepFunction">The step function to execute.</param>
    /// <exception cref="ArgumentNullException"></exception>
    public KernelDelegateProcessStep(StepFunction stepFunction)
    {
        this._stepFunction = stepFunction ?? throw new ArgumentNullException(nameof(stepFunction));
    }

    /// <summary>
    /// Invokes the step function with the provided kernel and context.
    /// </summary>
    /// <param name="kernel">The kernel instance used for processing.</param>
    /// <param name="context">The context for the step execution.</param>
    [KernelFunction(FunctionName)]
    public Task InvokeAsync(Kernel kernel, KernelProcessStepContext context) => this._stepFunction(kernel, context);
}
