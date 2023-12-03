// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

internal class AgentAssistantModel
{
    public IAgent Agent { get; set; }

    public string Description { get; set; }

    public string InputDescription { get; set; }

}
