// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Core.Responses;

public interface ITextGenerationResponse
{
    IReadOnlyList<TextContent> GetResults();
}
