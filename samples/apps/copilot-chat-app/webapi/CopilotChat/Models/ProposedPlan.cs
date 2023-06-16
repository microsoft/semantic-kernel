// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Planning;

namespace SemanticKernel.Service.CopilotChat.Models;

// Type of Plan
public enum PlanType
{
    Action, // single-step
    Sequential, // multi-step
}

// State of Plan
public enum PlanState
{
    NoOp, // Plan has not received any user input
    Approved,
    Rejected,
}

/// <summary>
/// Information about a single proposed plan.
/// </summary>
public class ProposedPlan
{
    /// <summary>
    /// Plan object to be approved or invoked.
    /// </summary>
    [JsonPropertyName("proposedPlan")]
    public Plan Plan { get; set; }

    /// <summary>
    /// Indicates whether plan is Action (single-step) or Sequential (multi-step).
    /// </summary>
    [JsonPropertyName("type")]
    public PlanType Type { get; set; }

    /// <summary>
    /// State of plan
    /// </summary>
    [JsonPropertyName("state")]
    public PlanState State { get; set; }

    /// <summary>
    /// Create a new proposed plan.
    /// </summary>
    /// <param name="plan">Proposed plan object</param>
    public ProposedPlan(Plan plan, PlanType type, PlanState state)
    {
        this.Plan = plan;
        this.Type = type;
        this.State = state;
    }
}
