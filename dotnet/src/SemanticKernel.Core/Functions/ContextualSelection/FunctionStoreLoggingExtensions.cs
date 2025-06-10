// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Functions;

[ExcludeFromCodeCoverage]
internal static class FunctionStoreLoggingExtensions
{
    internal static void LogFunctionsVectorizationInfo(this ILogger logger, IList<FunctionStore.FunctionVectorizationInfo> vectorizationInfo)
    {
        logger.LogInformation("ContextualFunctionProvider: Number of function to vectorize: {Count}", vectorizationInfo.Count);

        if (logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("ContextualFunctionProvider: Functions vectorization info: {VectorizationInfo}",
                string.Join(", ", vectorizationInfo.Select(info => $"\"Function: {info.Name}, VectorizationSource: {info.VectorizationSource}\"")));
        }
    }

    internal static void LogFunctionsSearchResults(this ILogger logger, string context, int maxNumberOfFunctionsToReturn, IList<VectorSearchResult<Dictionary<string, object?>>> results)
    {
        logger.LogInformation("ContextualFunctionProvider: Search returned {Count} functions, with a maximum limit of {MaxCount}", results.Count, maxNumberOfFunctionsToReturn);

        if (logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("ContextualFunctionProvider: Functions search results for context {Context} with a maximum limit of {MaxCount}: {Results}",
                $"\"{context}\"",
                maxNumberOfFunctionsToReturn,
                string.Join(", ", results.Select(result => $"\"Function: {result.Record["Name"]}, Score: {result.Score}\"")));
        }
    }
}
