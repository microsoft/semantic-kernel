// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// %%% COMMENT
/// </summary>
/// <param name="activity"></param>
/// <param name="engine"></param>
/// <returns></returns>
public delegate Task ActivityNotificationHandler(ActivityTemplateBase activity, RecalcEngine engine);

/// <summary>
/// %%% COMMENT
/// </summary>
public sealed class ProcessActionEnvironment
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    internal static ProcessActionEnvironment Default { get; } = new();

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public int MaximumExpressionLength { get; init; } = 3000;

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="activity"></param>
    /// <param name="engine"></param>
    /// <returns></returns>
    public Task ActivityNotificationHandler(ActivityTemplateBase activity, RecalcEngine engine) // %%% TODO: CONFIGURABLE
    {
        Console.WriteLine($"\nACTIVITY: {activity.GetType().Name}");

        if (activity is MessageActivityTemplate messageActivity)
        {
            if (!string.IsNullOrEmpty(messageActivity.Summary))
            {
                Console.WriteLine($"\t{messageActivity.Summary}"); // %%% DEVTRACE
            }

            string? activityText = engine.Format(messageActivity.Text);
            Console.WriteLine(activityText + Environment.NewLine); // %%% DEVTRACE
        }

        return Task.CompletedTask;
    }
}
