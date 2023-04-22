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
    private readonly IOrganizationHierarchyConnector _connector;

    public OrganizationHierarchySkill(IOrganizationHierarchyConnector connector)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
    }

    /// <summary>
    /// Get the email of the manager of the current user.
    /// </summary>
    [SKFunction("Get my manager's email address.")]
    public async Task<string> GetMyManagerEmailAsync(SKContext context)
        => await this._connector.GetManagerEmailAsync(context.CancellationToken);

    /// <summary>
    /// Get the name of the manager of the current user.
    /// </summary>
    [SKFunction("Get my manager's name.")]
    public async Task<string> GetMyManagerNameAsync(SKContext context)
        => await this._connector.GetManagerNameAsync(context.CancellationToken);
}
