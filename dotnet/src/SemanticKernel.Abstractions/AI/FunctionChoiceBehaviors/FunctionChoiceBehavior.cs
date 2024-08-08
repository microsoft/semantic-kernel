// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the base class for different function choice behaviors.
/// </summary>
public abstract class FunctionChoiceBehavior
{
    /// <summary>Returns the configuration specified by the <see cref="FunctionChoiceBehavior"/>.</summary>
    /// <param name="context">The function choice caller context.</param>
    /// <returns>The configuration.</returns>
    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context);
}
