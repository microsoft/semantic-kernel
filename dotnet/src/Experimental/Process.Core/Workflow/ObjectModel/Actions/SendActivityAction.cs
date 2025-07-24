// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SendActivityAction : ProcessAction<SendActivity>
{
    private readonly TextWriter _activityWriter;

    public SendActivityAction(SendActivity source, TextWriter activityWriter)
        : base(source)
    {
        if (source.Activity is null)
        {
            throw new InvalidActionException($"{nameof(SendActivity)} action must have an activity defined.");
        }

        this._activityWriter = activityWriter;
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        Console.WriteLine($"\nACTIVITY: {this.Model.Activity?.GetType().Name ?? "Unknown"}"); // %%% LOGGER

        if (this.Model.Activity is MessageActivityTemplate messageActivity)
        {
            if (!string.IsNullOrEmpty(messageActivity.Summary))
            {
                this._activityWriter.WriteLine($"\t{messageActivity.Summary}");
            }

            string? activityText = context.Engine.Format(messageActivity.Text);
            this._activityWriter.WriteLine(activityText + Environment.NewLine);
        }

        return Task.CompletedTask;
    }
}
