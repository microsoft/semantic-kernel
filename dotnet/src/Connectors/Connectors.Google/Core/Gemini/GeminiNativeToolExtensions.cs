// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Google.Core.Gemini;
internal static class GeminiNativeToolExtensions
{
    public static bool ValidateGeminiNativeTools(this GeminiNativeToolCallConfig? callConfig, GeminiRequest request)
    {
        if (callConfig is null)
        {
            return false;
        }

        bool hasAnyTool = callConfig.FileSearch is not null;
        // ... || callConfig.Grounding is not null;

        if (!hasAnyTool)
        {
            return false;
        }

        // Example: If FileSearch is present, check that its required fields adhere to the schema.
        if (callConfig.FileSearch is not null)
        {
            // Placeholder for future format checking (e.g., regex against store names)
            if (callConfig.FileSearch.FileReferences?.Count == 0)
            {
                // throw an exception or return false here.
                throw new InvalidOperationException("You need to supply at least one FileReference for a FileSearch");
            }
        }

        return true;
    }
}
