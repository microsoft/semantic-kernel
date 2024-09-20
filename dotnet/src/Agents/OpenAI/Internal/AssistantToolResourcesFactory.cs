﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

/// <summary>
/// Factory for creating <see cref="ToolResources"/> definition.
/// </summary>
/// <remarks>
/// Improves testability.
/// </remarks>
internal static class AssistantToolResourcesFactory
{
    /// <summary>
    /// Produces a <see cref="ToolResources"/> definition based on the provided parameters.
    /// </summary>
    /// <param name="vectorStoreId">An optional vector-store-id for the 'file_search' tool</param>
    /// <param name="codeInterpreterFileIds">An optionallist of file-identifiers for the 'code_interpreter' tool.</param>
    public static ToolResources? GenerateToolResources(string? vectorStoreId, IReadOnlyList<string>? codeInterpreterFileIds)
    {
        bool hasVectorStore = !string.IsNullOrWhiteSpace(vectorStoreId);
        bool hasCodeInterpreterFiles = (codeInterpreterFileIds?.Count ?? 0) > 0;

        ToolResources? toolResources = null;

        if (hasVectorStore || hasCodeInterpreterFiles)
        {
            toolResources =
                new ToolResources()
                {
                    FileSearch =
                        hasVectorStore ?
                            new FileSearchToolResources()
                            {
                                VectorStoreIds = [vectorStoreId!],
                            } :
                            null,
                    CodeInterpreter =
                        hasCodeInterpreterFiles ?
                            new CodeInterpreterToolResources()
                            {
                                FileIds = (IList<string>)codeInterpreterFileIds!,
                            } :
                            null,
                };
        }

        return toolResources;
    }
}
