// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Interface for common telemetry events to track actions across the semantic kernel.
/// </summary>
public interface ITelemetryService
{
    /// <summary>
    /// Creates a telemetry event when a skill function is executed.
    /// </summary>
    /// <param name="skillName">Name of the skill</param>
    /// <param name="functionName">Skill function name</param>
    /// <param name="success">If the skill executed successfully</param>
    void TrackSkillFunction(string skillName, string functionName, bool success);
}
