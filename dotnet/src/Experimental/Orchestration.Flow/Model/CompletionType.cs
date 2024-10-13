// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624

/// <summary>
/// The completion type of step
/// </summary>
public enum CompletionType
{
    /// <summary>
    /// Once
    /// </summary>
    Once,

    /// <summary>
    /// Optional
    /// </summary>
    Optional,

    /// <summary>
    /// At least once
    /// </summary>
    AtLeastOnce,

    /// <summary>
    /// Optional or multiple times
    /// </summary>
    ZeroOrMore,
}
