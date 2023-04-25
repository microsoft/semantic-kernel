// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Organizational Hierarchy skill.
/// </summary>
public class OrganizationHierarchySkill
{
    private readonly IOrganizationHierarchyAdapter _adapter;

    public OrganizationHierarchySkill(IOrganizationHierarchyAdapter adapter)
    {
        Ensure.NotNull(adapter, nameof(adapter));

        this._adapter = adapter;
    }

    /// <summary>
    /// Get the email of the manager of the current user.
    /// </summary>
    [SKFunction("Get my manager's email address.")]
    public async Task<string> GetMyManagerEmailAsync(SKContext context)
        => await this._adapter.GetManagerEmailAsync(context.CancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Get the name of the manager of the current user.
    /// </summary>
    [SKFunction("Get my manager's name.")]
    public async Task<string> GetMyManagerNameAsync(SKContext context)
        => await this._adapter.GetManagerNameAsync(context.CancellationToken).ConfigureAwait(false);
}
