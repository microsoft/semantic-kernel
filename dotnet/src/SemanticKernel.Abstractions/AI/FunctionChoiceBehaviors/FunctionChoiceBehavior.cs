// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the base class for different function choice behaviors.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "type")]
[JsonDerivedType(typeof(AutoFunctionChoiceBehavior), typeDiscriminator: AutoFunctionChoiceBehavior.TypeDiscriminator)]
[JsonDerivedType(typeof(RequiredFunctionChoiceBehavior), typeDiscriminator: RequiredFunctionChoiceBehavior.TypeDiscriminator)]
[JsonDerivedType(typeof(NoneFunctionChoiceBehavior), typeDiscriminator: NoneFunctionChoiceBehavior.TypeDiscriminator)]
[Experimental("SKEXP0001")]
public abstract class FunctionChoiceBehavior
{
    /// <summary>
    /// The default maximum number of function auto-invokes that can be made in a single user request.
    /// </summary>
    /// <remarks>
    /// After this number of iterations as part of a single user request is reached, auto-invocation
    /// will be disabled. This is a safeguard against possible runaway execution if the model routinely re-requests
    /// the same function over and over.
    /// </remarks>
    protected const int DefaultMaximumAutoInvokeAttempts = 5;

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' function information.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior AutoFunctionChoice(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true)
    {
        return new AutoFunctionChoiceBehavior(functions ?? [])
        {
            MaximumAutoInvokeAttempts = autoInvoke ? DefaultMaximumAutoInvokeAttempts : 0
        };
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior forces the model to always call one or more functions. The model will then select which function(s) to call.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' function information.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior RequiredFunctionChoice(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true)
    {
        return new RequiredFunctionChoiceBehavior(functions ?? [])
        {
            MaximumAutoInvokeAttempts = autoInvoke ? DefaultMaximumAutoInvokeAttempts : 0
        };
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior forces the model to not call any functions and only generate a user-facing message.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' function information.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    /// <remarks>
    /// Although this behavior prevents the model from calling any functions, the model can use the provided function information
    /// to describe how it would complete the prompt if it had the ability to call the functions.
    /// </remarks>
    public static FunctionChoiceBehavior NoneFunctionChoice(IEnumerable<KernelFunction>? functions = null)
    {
        return new NoneFunctionChoiceBehavior(functions ?? []);
    }

    /// <summary>Returns the configuration specified by the <see cref="FunctionChoiceBehavior"/>.</summary>
    /// <param name="context">The caller context.</param>
    /// <returns>The configuration.</returns>
    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context);
}
