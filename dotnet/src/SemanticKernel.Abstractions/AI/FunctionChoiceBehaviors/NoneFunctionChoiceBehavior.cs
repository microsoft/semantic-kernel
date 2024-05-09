// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that does not provides any <see cref="Kernel"/>'s plugins' function information to the model.
/// This behavior forces the model to not call any functions and only generate a user-facing message.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// This class type discriminator used for polymorphic deserialization of the type specified in JSON and YAML prompts.
    /// </summary>
    public const string TypeDiscriminator = "none";

    /// <inheritdoc/>
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        return new FunctionChoiceBehaviorConfiguration()
        {
            // By not providing either available or required functions, we are telling the model to not call any functions.
            AvailableFunctions = null,
            RequiredFunctions = null,
        };
    }
}
