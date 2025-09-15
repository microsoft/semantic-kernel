// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.MsGraph.Diagnostics;

namespace Microsoft.SemanticKernel.Plugins.MsGraph;

/// <summary>
/// Organizational Hierarchy plugin.
/// Provides methods to get information about the organization hierarchy, such as direct reports and manager details.
/// </summary>
public sealed class OrganizationHierarchyPlugin
{
    private readonly IOrganizationHierarchyConnector _connector;
    private readonly JsonSerializerOptions? _jsonSerializerOptions;
    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    /// <summary>
    /// Initializes a new instance of the <see cref="OrganizationHierarchyPlugin"/> class.
    /// </summary>
    /// <param name="connector">The connector to be used for fetching organization hierarchy data.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to use for serialization. If null, default options will be used.</param>
    public OrganizationHierarchyPlugin(IOrganizationHierarchyConnector connector, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        Ensure.NotNull(connector, nameof(connector));

        this._jsonSerializerOptions = jsonSerializerOptions ?? s_options;
        this._connector = connector;
    }

    /// <summary>
    /// Get the emails of the direct reports of the current user.
    /// </summary>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>A JSON string containing the email addresses of the direct reports of the current user.</returns>
    [KernelFunction, Description("Get my direct report's email addresses.")]
    public async Task<string> GetMyDirectReportsEmailAsync(CancellationToken cancellationToken = default)
        => JsonSerializer.Serialize(await this._connector.GetDirectReportsEmailAsync(cancellationToken).ConfigureAwait(false), this._jsonSerializerOptions);

    /// <summary>
    /// Get the email of the manager of the current user.
    /// </summary>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>A string containing the email address of the manager of the current user.</returns>
    [KernelFunction, Description("Get my manager's email address.")]
    public async Task<string?> GetMyManagerEmailAsync(CancellationToken cancellationToken = default)
        => await this._connector.GetManagerEmailAsync(cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Get the name of the manager of the current user.
    /// </summary>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to observe while waiting for the task to complete.</param>
    /// <returns>A string containing the name of the manager of the current user.</returns>
    [KernelFunction, Description("Get my manager's name.")]
    public async Task<string?> GetMyManagerNameAsync(CancellationToken cancellationToken = default)
        => await this._connector.GetManagerNameAsync(cancellationToken).ConfigureAwait(false);
}
