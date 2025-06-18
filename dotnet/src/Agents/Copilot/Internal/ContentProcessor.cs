// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.CopilotStudio.Internal;

internal static class ContentProcessor
{
    internal static IEnumerable<StreamingKernelContent> ConvertToStreaming(ChatMessageContentItemCollection items, ILogger logger)
    {
        foreach (KernelContent item in items)
        {
            if (item is TextContent textContent)
            {
                yield return new StreamingTextContent(textContent.Text)
                {
                    Encoding = textContent.Encoding,
                    InnerContent = textContent.InnerContent,
                    Metadata = textContent.Metadata,
                };
            }
            else if (item is ReasoningContent reasoningContent)
            {
                yield return new StreamingReasoningContent(reasoningContent.Text);
            }
            else if (item is ActionContent actionContent)
            {
                yield return new StreamingActionContent(actionContent.Text);
            }
            else
            {
                logger.LogWarning("Unknown content type '{ContentType}' received.", item.GetType().Name);
            }
        }
    }
}
