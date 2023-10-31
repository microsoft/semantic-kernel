// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;

namespace NCalcPlugins;

/// <summary>
/// Simple calculator plugin that evaluates a mathematical expression.
/// </summary>
public class SimpleCalculatorPlugin
{
    private readonly ISKFunction _mathTranslator;

    private static readonly string[] s_stopSequences = new[] { "Problem:", "Solution:" };

    /// <summary>
    /// Initializes a new instance of the <see cref="SimpleCalculatorPlugin"/> class.
    /// </summary>
    /// <param name="kernel">The kernel used to create the semantic function.</param>
    public SimpleCalculatorPlugin(IKernel kernel)
    {
        this._mathTranslator = kernel.CreateSemanticFunction(
            "Task: Give the final solution for the problem. Be as concise as possible.\nProblem:4+4\nSolution:8\nProblem:{{$input}}\nSolution:\n",
            pluginName: nameof(SimpleCalculatorPlugin),
            functionName: "Calculator",
            description: "Evaluate a mathematical expression. Input is a valid mathematical expression that could be executed by a simple calculator i.e. add, subtract, multiply and divide. Cannot use variables.",
            requestSettings: new AIRequestSettings()
            {
                ExtensionData = new Dictionary<string, object>()
                {
                    { "MaxTokens", 256 },
                    { "Temperature", 0.0 },
                    { "StopSequences", s_stopSequences },
                }
            });
    }
}
