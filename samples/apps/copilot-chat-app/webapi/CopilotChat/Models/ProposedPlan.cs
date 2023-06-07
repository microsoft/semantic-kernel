// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Planning;

namespace SemanticKernel.Service.CopilotChat.Models;

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
    /// Indicates whether plan is Action (single-step) or Sequential (multi-step)
    /// </summary>
    public string Type { get; set; }

    /// <summary>
    /// Indicates whether the user editted plan inputs or steps before approving
    /// </summary>
    public Boolean? HasEdits { get; set; }

    /// <summary>
    /// Create a new proposed plan.
    /// </summary>
    /// <param name="plan">Proposed plan object</param>
    public ProposedPlan(Plan plan, string type)
    {
        this.Plan = plan;
        this.Type = type;
    }

    /// <summary>
    /// Create a new proposed plan.
    /// </summary>
    /// <param name="plan">Proposed plan object</param>
    public ProposedPlan(Plan plan, string type, Boolean hasEdits)
    {
        this.Plan = plan;
        this.Type = type;
        this.HasEdits = hasEdits;
    }
}
