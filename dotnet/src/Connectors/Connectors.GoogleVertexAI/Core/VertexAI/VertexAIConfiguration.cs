// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

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
