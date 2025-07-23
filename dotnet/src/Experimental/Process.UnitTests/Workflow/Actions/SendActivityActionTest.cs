// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.SemanticKernel.Process.Workflows.Actions;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

/// <summary>
/// Tests for <see cref="SendActivityAction"/>.
/// </summary>
public sealed class SendActivityActionTest(ITestOutputHelper output) : ProcessActionTest(output)
{
    [Fact]
    public async Task CaptureActivity()
    {
        // Arrange
        ActivitySink activitySink = new();
        SendActivity model =
            this.CreateModel(
                this.FormatDisplayName(nameof(CaptureActivity)),
                "Test activity message");

        // Act
        SendActivityAction action = new(model, activitySink.Handler);
        await this.ExecuteAction(action);

        // Assert
        this.VerifyModel(model, action);
        Assert.Single(activitySink.Activities);
    }

    private SendActivity CreateModel(string displayName, string activityMessage, string? summary = null)
    {
        MessageActivityTemplate.Builder activityBuilder =
            new()
            {
                Summary = summary,
                Text = { TemplateLine.Parse(activityMessage) },
            };
        SendActivity.Builder actionBuilder =
            new()
            {
                Id = this.CreateActionId(),
                DisplayName = this.FormatDisplayName(displayName),
                Activity = activityBuilder.Build(),
            };

        SendActivity model = this.AssignParent<SendActivity>(actionBuilder);

        return model;
    }

    private sealed class ActivitySink
    {
        public List<ActivityTemplateBase> Activities { get; } = [];

        public Task Handler(ActivityTemplateBase activity, RecalcEngine engine)
        {
            this.Activities.Add(activity);

            return Task.CompletedTask;
        }
    }
}
