// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Planning;

namespace SemanticKernel.Service;

public class CopilotChatPlanner
{
    private readonly SequentialPlanner _sequentialPlanner;

    public CopilotChatPlanner(
        SequentialPlanner  sequentialPlanner
        )
    {
        this._sequentialPlanner = sequentialPlanner;
    }
}
