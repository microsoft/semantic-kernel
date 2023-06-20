// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

/// <summary>
/// Organizational Hierarchy skill.
/// </summary>
public sealed class OrganizationHierarchySkill
{
    private readonly IOrganizationHierarchyConnector _connector;

    public OrganizationHierarchySkill(IOrganizationHierarchyConnector connector)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._connector = connector;
    }

    /// <summary>
    /// Get the emails of the direct reports of the current user.
    /// </summary>
    [SKFunction, Description("Get my direct report's email addresses.")]
    public async Task<string> GetMyDirectReportsEmailAsync(CancellationToken cancellationToken = default)
        => JsonSerializer.Serialize(await this._connector.GetDirectReportsEmailAsync(cancellationToken).ConfigureAwait(false));

    /// <summary>
    /// Get the email of the manager of the current user.
    /// </summary>
    [SKFunction, Description("Get my manager's email address.")]
    public async Task<string> GetMyManagerEmailAsync(CancellationToken cancellationToken = default)
        => await this._connector.GetManagerEmailAsync(cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Get the name of the manager of the current user.
    /// </summary>
    [SKFunction, Description("Get my manager's name.")]
    public async Task<string> GetMyManagerNameAsync(CancellationToken cancellationToken = default)
        => await this._connector.GetManagerNameAsync(cancellationToken).ConfigureAwait(false);
}
