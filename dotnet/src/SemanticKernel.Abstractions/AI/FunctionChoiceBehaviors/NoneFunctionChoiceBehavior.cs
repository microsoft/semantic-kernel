// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that does not provides any <see cref="Kernel"/>'s plugins' function information to the model.
/// This behavior forces the model to not call any functions and only generate a user-facing message.
/// </summary>
public sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// The class alias. Used as a value for the discriminator property for polymorphic deserialization
    /// of function choice behavior specified in JSON and YAML prompts.
    /// </summary>
    public const string Alias = "none";

    /// <inheritdoc/>
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        return new FunctionChoiceBehaviorConfiguration()
        {
            // By not providing either available or required functions, we are telling the model to not call any functions.
            MaximumAutoInvokeAttempts = 0, // Disable unnecessary auto-invocation
        };
    }
}
