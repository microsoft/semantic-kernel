// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Represents the vetting level of a connector against a prompt type.
/// </summary>
public enum VettingLevel
{
    // TODO: Decouple Vetting Func or/and allow for more nuanced Vetting levels introducing quantitative evaluations (percentage of chance to succeed / to recover the correct result / entropy / results comparisons etc.)
    Invalid = -1,
    None = 0,
    Oracle = 1,
    OracleVaried = 2 // Oracle varied means distinct prompts were used for vetting tests.
}
