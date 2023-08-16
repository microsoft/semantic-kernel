// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Linq;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector;
using SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion.ArithmeticMocks;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class MultiTextCompletionSettingsTests : MultiConnectorTestsBase
{
    public MultiTextCompletionSettingsTests(ITestOutputHelper output) : base(output) { }

    [Theory]
    [InlineData(true, false, "default")]
    [InlineData(false, true, null)]
    public void GetPromptSettingsWithAndWithoutFreezePromptTypesShouldHandleSettingsAppropriately(bool freezePromptTypes, bool isNewExpected, string expectedPromptName)
    {
        // Arrange
        var sampleJobs = this.CreateSampleJobs(new[] { ArithmeticOperation.Add }, 1, 2);
        var completionJob = sampleJobs.First();

        var multiTextCompletionSettings = new MultiTextCompletionSettings { FreezePromptTypes = freezePromptTypes, PromptTruncationLength = 10 };

        // Act
        var result = multiTextCompletionSettings.GetPromptSettings(completionJob, out bool isNew);

        // Assert
        Assert.Equal(isNewExpected, isNew);

        if (expectedPromptName != null)
        {
            Assert.Equal(expectedPromptName, result.PromptType.PromptName);
        }
        else
        {
            // Additional asserts based on expected behavior when there is no match.
            // If there aren't any other asserts, you can remove this section.
        }
    }

    [Theory]
    [InlineData(true, true, false)]
    [InlineData(false, true, true)]
    public void GetPromptSettingsWithAndWithoutSignatureAdjustmentShouldHandleSignaturesAppropriately(bool adjustPromptStarts, bool isFirstSignatureNew, bool areSignaturesEqual)
    {
        var firstDigit = 3;

        // Arrange
        var firstMultiplyJob = this.CreateSampleJobs(new[] { ArithmeticOperation.Multiply }, firstDigit, 4).First();
        var secondMultiplyJob = this.CreateSampleJobs(new[] { ArithmeticOperation.Multiply }, 2, 8).First();

        var truncationLength = 3;
        var multiTextCompletionSettings = new MultiTextCompletionSettings() { PromptTruncationLength = truncationLength, AdjustPromptStarts = adjustPromptStarts };

        // Act
        var firstSignature = multiTextCompletionSettings.GetPromptSettings(firstMultiplyJob, out bool isNew).PromptType.Signature.PromptStart;
        var signatureAdjusted = multiTextCompletionSettings.GetPromptSettings(secondMultiplyJob, out bool isNew2).PromptType.Signature.PromptStart;

        // Assert
        Assert.Equal(isFirstSignatureNew, isNew);

        if (areSignaturesEqual)
        {
            Assert.Equal(firstSignature, signatureAdjusted);
        }
        else
        {
            Assert.NotEqual(firstSignature, signatureAdjusted);
        }

        if (adjustPromptStarts)
        {
            Assert.Equal(firstMultiplyJob.Prompt.IndexOf(firstDigit.ToString(CultureInfo.InvariantCulture), StringComparison.Ordinal), signatureAdjusted.Length);
        }
        else
        {
            Assert.Equal(truncationLength, firstSignature.Length);
        }
    }
}
