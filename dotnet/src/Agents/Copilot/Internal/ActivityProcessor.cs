// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Agents.Core.Models;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.CopilotStudio.Internal;

internal static class ActivityProcessor
{
    public static async IAsyncEnumerable<ChatMessageContent> ProcessActivity(IAsyncEnumerable<IActivity> activities, ILogger logger)
    {
        await foreach (IActivity activity in activities.ConfigureAwait(false))
        {
            switch (activity.Type)
            {
                case "message":
                    yield return
                        new(AuthorRole.Assistant, items: [.. GetMessageItems(activity)])
                        {
                            InnerContent = activity
                        };
                    break;
                case "typing":
                    yield return
                        new(AuthorRole.Assistant, items: [new ReasoningContent()])
                        {
                            InnerContent = activity
                        };
                    break;
                case "event":
                    break;
                default:
                    logger.LogWarning("Unknown activity type '{ActivityType}' received.", activity.Type);
                    break;
            }
        }

        static IEnumerable<KernelContent> GetMessageItems(IActivity activity)
        {
            yield return new TextContent(activity.Text);
            foreach (CardAction action in activity.SuggestedActions?.Actions ?? [])
            {
                yield return new ActionContent(action.Title);
            }
        }
    }
}
