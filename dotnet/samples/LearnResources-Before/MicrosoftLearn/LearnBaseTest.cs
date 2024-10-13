// Copyright (c) Microsoft. All rights reserved.

namespace Examples;

public abstract class LearnBaseTest : BaseTest
{
    protected List<string> SimulatedInputText = [];
    protected int SimulatedInputTextIndex = 0;

    protected LearnBaseTest(List<string> simulatedInputText, ITestOutputHelper output) : base(output)
    {
        SimulatedInputText = simulatedInputText;
    }

    protected LearnBaseTest(ITestOutputHelper output) : base(output)
    {
    }

    /// <summary>
    /// Simulates reading input strings from a user for the purpose of running tests.
    /// </summary>
    /// <returns>A simulate user input string, if available. Null otherwise.</returns>
    public string? ReadLine()
    {
        if (SimulatedInputTextIndex < SimulatedInputText.Count)
        {
            return SimulatedInputText[SimulatedInputTextIndex++];
        }

        return null;
    }
}

public static class BaseTestExtensions
{
    /// <summary>
    /// Simulates reading input strings from a user for the purpose of running tests.
    /// </summary>
    /// <returns>A simulate user input string, if available. Null otherwise.</returns>
    public static string? ReadLine(this BaseTest baseTest)
    {
        var learnBaseTest = baseTest as LearnBaseTest;

        if (learnBaseTest is not null)
        {
            return learnBaseTest.ReadLine();
        }

        return null;
    }
}
