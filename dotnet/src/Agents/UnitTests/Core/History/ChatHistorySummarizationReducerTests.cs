// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.History;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.History;

/// <summary>
/// %%%
/// </summary>
public class ChatHistorySummarizationReducerTests
{
    /// <summary>
    /// %%%
    /// </summary>
    [Theory]
    [InlineData(-1)]
    [InlineData(-1, int.MaxValue)]
    [InlineData(int.MaxValue, -1)]
    public void VerifyChatHistoryConstructorArgumentValidation(int targetCount, int? thresholdCount = null)
    {
        Assert.Throws<ArgumentException>(() => new ChatHistorySummarizationReducer(new(), targetCount, thresholdCount));
    }

    /// <summary>
    /// %%%
    /// </summary>
    [Fact]
    public void VerifyChatHistoryHasCode()
    {
        HashSet<ChatHistorySummarizationReducer> reducers = [];

        int hashCode1 = GenerateHashCode(3, 4);
        int hashCode2 = GenerateHashCode(33, 44);
        int hashCode3 = GenerateHashCode(3000, 4000);

        Assert.NotEqual(hashCode1, hashCode2);
        Assert.NotEqual(hashCode2, hashCode3);
        Assert.Equal(3, reducers.Count);

        int GenerateHashCode(int targetCount, int thresholdCount)
        {
            ChatHistorySummarizationReducer reducer = new(new(), targetCount, thresholdCount);

            reducers.Add(reducer);

            return reducer.GetHashCode();
        }
    }
}
