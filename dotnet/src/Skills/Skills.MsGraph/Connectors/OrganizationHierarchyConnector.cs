// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Graph;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors;

/// <summary>
/// Connector for Microsoft Graph API for organizational hierarchy.
/// </summary>
public class OrganizationHierarchyConnector : IOrganizationHierarchyConnector
{
    private readonly GraphServiceClient _graphServiceClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="OrganizationHierarchyConnector"/> class.
    /// </summary>
    /// <param name="graphServiceClient">A graph service client.</param>
    public OrganizationHierarchyConnector(GraphServiceClient graphServiceClient)
    {
        this._graphServiceClient = graphServiceClient;
    }

    /// <inheritdoc/>
    public async Task<string> GetManagerEmailAsync(CancellationToken cancellationToken = default) =>
        ((User)await this._graphServiceClient.Me
            .Manager
            .Request().GetAsync(cancellationToken).ConfigureAwait(false)).UserPrincipalName;

    /// <inheritdoc/>
    public async Task<string> GetManagerNameAsync(CancellationToken cancellationToken = default) =>
        ((User)await this._graphServiceClient.Me
            .Manager
            .Request().GetAsync(cancellationToken).ConfigureAwait(false)).DisplayName;

    /// <inheritdoc/>
    public async Task<IEnumerable<string>> GetDirectReportsEmailAsync(CancellationToken cancellationToken = default)
    {
        IUserDirectReportsCollectionWithReferencesPage directsPage = await this._graphServiceClient.Me
            .DirectReports
            .Request().GetAsync(cancellationToken).ConfigureAwait(false);

        List<User> directs = directsPage.Cast<User>().ToList();

        while (directs.Count != 0 && directsPage.NextPageRequest != null)
        {
            directsPage = await directsPage.NextPageRequest.GetAsync(cancellationToken).ConfigureAwait(false);
            directs.AddRange(directsPage.Cast<User>());
        }

        return directs.Select(d => d.UserPrincipalName);
    }
}
