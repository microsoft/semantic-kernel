// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;

namespace NCalcPlugins;

/// <summary>
/// Simple calculator skill that evaluates a mathematical expression.
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
            skillName: nameof(SimpleCalculatorPlugin),
            functionName: "Calculator",
            description: "Evaluate a mathematical expression. Input is a valid mathematical expression that could be executed by a simple calculator i.e. add, subtract, multiply and divide. Cannot use variables.",
            maxTokens: 256,
            temperature: 0.0,
            topP: 1,
            stopSequences: s_stopSequences);
    }
}
