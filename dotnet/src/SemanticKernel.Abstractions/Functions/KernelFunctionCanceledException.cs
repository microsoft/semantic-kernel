// Copyright (c) Microsoft. All rights reserved.

using System;

#pragma warning disable RCS1194 // Implement exception constructors.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an <see cref="OperationCanceledException"/>-derived exception type
/// that's thrown from a <see cref="KernelFunction"/> invocation when a <see cref="Kernel"/>
/// event handler (e.g. <see cref="Kernel.FunctionInvoked"/>) requests cancellation.
/// </summary>
public sealed class KernelFunctionCanceledException : OperationCanceledException
{
    /// <summary>Initializes the exception instance.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> passed to the invocation of <paramref name="function"/>.</param>
    /// <param name="function">The <see cref="KernelFunction"/> whose invocation was canceled.</param>
    /// <param name="arguments">The arguments collection supplied to the invocation of <paramref name="function"/>.</param>
    /// <param name="functionResult">
    /// The result of the <see cref="KernelFunction"/> invocation, potentially modified by the event handler,
    /// if cancellation was requested after the function's successful completion.
    /// </param>
    /// <param name="innerException">The exception that is the cause of the current exception.</param>
    public KernelFunctionCanceledException(
        Kernel kernel, KernelFunction function, KernelArguments arguments,
        FunctionResult? functionResult, Exception? innerException = null) :
        base($"The invocation of function '{function.Name}' was canceled.", innerException, (innerException as OperationCanceledException)?.CancellationToken ?? default)
    {
        this.Kernel = kernel;
        this.Function = function;
        this.Arguments = arguments;
        this.FunctionResult = functionResult;
    }

    /// <summary>Gets the <see cref="Kernel"/> that was passed to the invocation of <see cref="Function"/>.</summary>
    public Kernel Kernel { get; }

    /// <summary>Gets the <see cref="KernelFunction"/> whose invocation was canceled.</summary>
    public KernelFunction Function { get; }

    /// <summary>Gets the arguments collection that was supplied to the invocation of <see cref="Function"/>.</summary>
    public KernelArguments Arguments { get; }

    /// <summary>Gets the result of the <see cref="KernelFunction"/> if it had completed execution before cancellation was requested.</summary>
    public FunctionResult? FunctionResult { get; }
}
