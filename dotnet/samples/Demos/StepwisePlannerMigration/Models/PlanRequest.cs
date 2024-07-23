// Copyright (c) Microsoft. All rights reserved.

namespace StepwisePlannerMigration.Models;

/// <summary>
/// Request model for planning endpoints.
/// </summary>
public class PlanRequest
{
    /// <summary>
    /// A goal which should be achieved after plan execution.
    /// </summary>
    public string Goal { get; set; }
}
