using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Planning;

namespace SemanticKernel.Service.Model;

/// <summary>
/// Information about a single proposed plan.
/// </summary>
public class ProposedPlan
{
    /// <summary>
    /// Plan object to be approved or invoked.
    /// </summary>
    [JsonPropertyName("proposedPlan")]
    public Plan plan { get; set; }

    /// <summary>
    /// Create a new proposed plan.
    /// </summary>
    /// <param name="plan">Proposed plan object</param>
    public ProposedPlan(Plan plan)
    {
        this.plan = plan;
    }
}
