#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.VertexAI;

internal sealed class VertexAIConfiguration
{
    public VertexAIConfiguration(string location, string projectId)
    {
        Verify.NotNullOrWhiteSpace(location);
        Verify.NotNullOrWhiteSpace(projectId);

        this.Location = location;
        this.ProjectId = projectId;
    }

    public string Location { get; }
    public string ProjectId { get; }
}
