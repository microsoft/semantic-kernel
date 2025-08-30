// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
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
        SendActivity model =
            this.CreateModel(
                this.FormatDisplayName(nameof(CaptureActivity)),
                "Test activity message");
        await using StringWriter activityWriter = new();

        // Act
        SendActivityAction action = new(model, activityWriter);
        await this.ExecuteAction(action);
        activityWriter.Flush();

        // Assert
        this.VerifyModel(model, action);
        Assert.NotEmpty(activityWriter.ToString());
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
}
