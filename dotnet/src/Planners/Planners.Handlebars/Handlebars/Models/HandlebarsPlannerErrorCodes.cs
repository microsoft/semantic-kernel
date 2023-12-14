// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Enum error codes for Handlebars planner exceptions.
/// </summary>
public enum HandlebarsPlannerErrorCodes
{
    /// <summary>
    /// Error code for hallucinated helpers.
    /// </summary>
    HallucinatedHelpers,

    /// <summary>
    /// Error code for invalid Handlebars template.
    /// </summary>
    InvalidTemplate,

    /// <summary>
    /// Error code for insufficient functions to complete the goal.
    /// </summary>
    InsufficientFunctionsForGoal,
}
