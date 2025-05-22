// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithTextSearchBehaviorConformance;

public abstract class AgentWithTextSearchProvider<TFixture>(Func<TFixture> createAgentFixture, ITestOutputHelper output) : IAsyncLifetime
    where TFixture : AgentFixture
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private TFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected TFixture Fixture => this._agentFixture;

    [Theory]
    // Private data.
    [InlineData("What was Acme Corp's revenue in Q1 2025?", "12.5", "Acme Corp reported a revenue of $12.5 million in Q1 2025.", "This represents a 15% increase from Q4 2024.")]
    [InlineData("What was BetaTech Inc.'s stock price on May 1, 2025?", "45.67", "The stock price of BetaTech Inc. closed at $45.67 on May 1, 2025.", "It saw a 3% increase from the previous day.")]
    [InlineData("What was Gamma Solutions' profit margin in FY 2024?", "22", "Gamma Solutions had a profit margin of 22% in FY 2024.", "This was an improvement from 18% in FY 2023.")]
    [InlineData("What is DeltaSoft's market share in the enterprise software sector?", "35", "DeltaSoft holds a 35% market share in the enterprise software sector.", "Its closest competitor holds 25%.")]
    // Generate knowledge.
    [InlineData("When was the Eiffel Tower completed?", "1889", "The Eiffel Tower was completed in 1889.", "It is located in Paris, France.")]
    [InlineData("At what temperature in Celsius does water boil?", "100", "Water boils at 212 degrees fahrenheit.", "Water boils at 100 degrees Celsius.")]
    [InlineData("What did Einstein say about imagination?", "Imagination is more important than knowledge", "Albert Einstein said, 'Imagination is more important than knowledge.'")]
    // Data contradicting Generate knowledge.
    [InlineData("When was the Eiffel Tower completed?", "2005", "The Eiffel Tower was completed in 2005.", "It is located in Paris, France.")]
    [InlineData("At what temperature in Celsius does water boil?", "150", "Water boils at 300 degrees fahrenheit.", "Water boils at 150 degrees Celsius.")]
    // Check for citations
    [InlineData("When was the Eiffel Tower completed?", "http://mydata.mycompany.com/dataset2", "It is located in Paris, France.", "The Eiffel Tower was completed in 1889.")]
    [InlineData("What was Gamma Solutions' profit margin in FY 2024?", "http://mydata.mycompany.com/dataset1", "Gamma Solutions had a profit margin of 22% in FY 2024.", "This was an improvement from 18% in FY 2023.")]
    [InlineData("When was the Eiffel Tower completed?", "DataSet2", "It is located in Paris, France.", "The Eiffel Tower was completed in 1889.")]
    [InlineData("What was Gamma Solutions' profit margin in FY 2024?", "DataSet1", "Gamma Solutions had a profit margin of 22% in FY 2024.", "This was an improvement from 18% in FY 2023.")]
    public async Task TextSearchBehaviorStateIsUsedByAgentInternalAsync(string question, string expectedResult, params string[] ragResults)
    {
        // Arrange
        ragResults.Select(x => new TextSearchResult(x)).ToAsyncEnumerable();
        var mockTextSearch = new Mock<ITextSearch>();
        mockTextSearch.Setup(x => x.GetTextSearchResultsAsync(
            It.IsAny<string>(),
            It.IsAny<TextSearchOptions>(),
            It.IsAny<CancellationToken>()))
            .ReturnsAsync(
                new KernelSearchResults<TextSearchResult>(ragResults.Select((x, i) => new TextSearchResult(x) { Name = $"DataSet{i + 1}", Link = $"http://mydata.mycompany.com/dataset{i + 1}" }).ToAsyncEnumerable()));

        var textSearchBehavior = new TextSearchProvider(mockTextSearch.Object);

        var agent = this.Fixture.Agent;

        var agentThread = this.Fixture.GetNewThread();

        try
        {
            agentThread.AIContextProviders.Add(textSearchBehavior);

            // Act
            var inputMessage = question;
            var asyncResults1 = agent.InvokeAsync(inputMessage, agentThread);
            var result = await asyncResults1.FirstAsync();

            // Assert
            output.WriteLine(result.Message.Content);
            Assert.Contains(expectedResult, result.Message.Content, StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            // Cleanup
            await this.Fixture.DeleteThread(agentThread);
        }
    }

    public Task InitializeAsync()
    {
        this._agentFixture = createAgentFixture();
        return this._agentFixture.InitializeAsync();
    }

    public Task DisposeAsync()
    {
        return this._agentFixture.DisposeAsync();
    }
}
