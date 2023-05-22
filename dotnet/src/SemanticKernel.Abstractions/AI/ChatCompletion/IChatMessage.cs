// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public interface IChatMessage
{
    string Role { get; }
    string Content { get; }
}
