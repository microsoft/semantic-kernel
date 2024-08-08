// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the base class for different function choice behaviors.
/// These behaviors define the way functions are chosen by LLM and various aspects of their invocation by AI connectors.
/// </summary>
public abstract class FunctionChoiceBehavior
{
    /// <summary>
    /// Returns the configuration used by AI connectors to determine function choice and invocation behavior.
    /// </summary>
    /// <param name="context">The context provided by AI connectors, used to determine the configuration.</param>
    /// <returns>The configuration.</returns>
    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context);
}
