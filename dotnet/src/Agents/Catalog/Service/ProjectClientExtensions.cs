// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// Extensions methods for the <see cref="AIProjectClient"/>.
/// </summary>
public static class ProjectClientExtensions
{
    /// <summary>
    /// Convenience method to retrieve the connection properties for the specified connection type.
    /// </summary>
    /// <param name="client">The foundry project lcient.</param>
    /// <param name="connectionType">The desired connection type (default: AzureOpenAI)</param>
    public static async Task<ConnectionProperties> GetConnectionAsync(this AIProjectClient client, ConnectionType connectionType = ConnectionType.AzureOpenAI)
    {
        ConnectionsClient connectionsClient = client.GetConnectionsClient();

        ConnectionResponse connection = await connectionsClient.GetDefaultConnectionAsync(connectionType, withCredential: true).ConfigureAwait(false);

        return connection.Properties;
    }
}
