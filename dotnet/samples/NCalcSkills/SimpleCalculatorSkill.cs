// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.SkillDefinition;

namespace NCalcSkills;

/// <summary>
/// Simple calculator skill that evaluates a mathematical expression.
/// </summary>
public class SimpleCalculatorSkill
{
    private readonly ISKFunction _mathTranslator;

    private static readonly string[] s_stopSequences = new[] { "Problem:", "Solution:" };

    /// <summary>
    /// Initializes a new instance of the <see cref="SimpleCalculatorSkill"/> class.
    /// </summary>
    /// <param name="kernel">The kernel used to create the semantic function.</param>
    public SimpleCalculatorSkill(IKernel kernel)
    {
        this._mathTranslator = kernel.CreateSemanticFunction(
            "Task: Give the final solution for the problem. Be as concise as possible.\nProblem:4+4\nSolution:8\nProblem:{{$input}}\nSolution:\n",
            skillName: nameof(SimpleCalculatorSkill),
            functionName: "Calculator",
            description: "Evaluate a mathematical expression. Input is a valid mathematical expression that could be executed by a simple calculator i.e. add, subtract, multiply and divide. Cannot use variables.",
            requestSettings: new { MaxTokens = 256, Temperature = 0.0, TopP = 1, StopSequences = s_stopSequences });
    }
}
