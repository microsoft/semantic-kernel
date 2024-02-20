// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIClassificationTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    private readonly ITestOutputHelper _output;

    public OpenAIClassificationTests(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Fact(Skip = "Manual verification")]
    public async Task ClassifyTextAsync()
    {
        // Arrange
        var connector = new OpenAITextClassificationService(
            modelId: this.ModelId,
            apiKey: this.ApiKey);

        // Act
        var result = await connector.ClassifyTextAsync("I am happy");

        // Assert
        Assert.NotNull(result);
        var openAIClassificationResult = result.Result as OpenAIClassificationResult;
        Assert.NotEmpty(openAIClassificationResult!.Entries);

        this._output.WriteLine($"Content flagged: {openAIClassificationResult.Flagged}");
        foreach (var entry in openAIClassificationResult.Entries)
        {
            this._output.WriteLine(entry.ToString());
        }
    }

    private string ModelId => this._configuration["OpenAIModeration:ModelId"]!;
    private string ApiKey => this._configuration["OpenAI:ApiKey"]!;
}
