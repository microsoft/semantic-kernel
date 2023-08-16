// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class PromptMultiConnectorSettingsTests : MultiConnectorTestsBase
{
    public PromptMultiConnectorSettingsTests(ITestOutputHelper output) : base(output) { }

    [Fact]
    public void SelectAppropriateTextCompletionShouldReturnHighestVettingLevel()
    {
        var settings = new PromptMultiConnectorSettings();

        // Mocked CompletionJob and comparer
        var completionJob = new CompletionJob();

        int MockComparer(CompletionJob job, PromptConnectorSettings setting1, PromptConnectorSettings setting2)
        {
            return setting2.VettingLevel.CompareTo(setting1.VettingLevel);
        }

        var completions = this.CreateCompletions(new(), TimeSpan.Zero, 0m, TimeSpan.Zero, 0m, null);

        settings.GetConnectorSettings(completions[0].Name).VettingLevel = VettingLevel.Oracle;
        settings.GetConnectorSettings(completions[1].Name).VettingLevel = VettingLevel.OracleVaried;

        var result = settings.SelectAppropriateTextCompletion(completionJob, completions, MockComparer);

        Assert.Equal(completions[1].Name, result.namedTextCompletion.Name); // The one with the highest VettingLevel should be returned
    }

    //[Fact]
    //public void IsSampleNeededShouldReturnTrueWhenConditionsMet()
    //{
    //    var settings = new PromptMultiConnectorSettings
    //    {
    //        PromptType = new PromptType { MaxInstanceNb = 10 }
    //    };

    //    var completions = this.CreateCompletions(new(), TimeSpan.Zero, 0m, TimeSpan.Zero, 0m, null); // 

    //    settings.GetConnectorSettings(completions[0].Name).VettingLevel = VettingLevel.None;

    //    var result = settings.IsSampleNeeded("TestPrompt", completions, true);
    //    Assert.True(result); // Conditions are met so should return true
    //}

    [Fact]
    public void GetCompletionsToTestShouldReturnCorrectCompletions()
    {
        var settings = new PromptMultiConnectorSettings();
        var completions = this.CreateCompletions(new(), TimeSpan.Zero, 0m, TimeSpan.Zero, 0m, null); // 

        var originalTest = new ConnectorTest() { ConnectorName = "Primary" };

        var completionsToTest = settings.GetCompletionsToTest(originalTest, completions, enablePrimaryCompletionTests: false);

        Assert.DoesNotContain(completionsToTest, x => x.Name == completions[0].Name);
        Assert.Contains(completionsToTest, x => x.Name == completions[1].Name);
    }
}
