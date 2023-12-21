// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using NCalc;

namespace NCalcPlugins;

/// <summary>
/// Plugin that enables the comprehension of mathematical problems presented in English / natural-language text, followed by the execution of the necessary calculations to solve those problems.
/// </summary>
public class LanguageCalculatorPlugin
{
    private readonly KernelFunction _mathTranslator;
    private const string MathTranslatorPrompt =
        @"Translate a math problem into a expression that can be executed using .net NCalc library. Use the output of running this code to answer the question.
Available functions: Abs, Acos, Asin, Atan, Ceiling, Cos, Exp, Floor, IEEERemainder, Log, Log10, Max, Min, Pow, Round, Sign, Sin, Sqrt, Tan, and Truncate. in and if are also supported.

Question: $((Question with math problem.))
expression:``` $((single line mathematical expression that solves the problem))```

[Examples]
Question: What is 37593 * 67?
expression:```37593 * 67```

Question: what is 3 to the 2nd power?
expression:```Pow(3, 2)```

Question: what is sine of 0 radians?
expression:```Sin(0)```

Question: what is sine of 45 degrees?
expression:```Sin(45 * Pi /180 )```

Question: how many radians is 45 degrees?
expression:``` 45 * Pi / 180 ```

Question: what is the square root of 81?
expression:```Sqrt(81)```

Question: what is the angle whose sine is the number 1?
expression:```Asin(1)```

[End of Examples]

Question: {{ $input }}
";

    /// <summary>
    /// Initializes a new instance of the <see cref="LanguageCalculatorPlugin"/> class.
    /// </summary>
    public LanguageCalculatorPlugin()
    {
        this._mathTranslator = KernelFunctionFactory.CreateFromPrompt(
            MathTranslatorPrompt,
            functionName: "TranslateMathProblem",
            description: "Used by 'Calculator' function.",
            executionSettings: new PromptExecutionSettings()
            {
                ExtensionData = new Dictionary<string, object>()
                {
                    { "MaxTokens", 256 },
                    { "Temperature", 0.0 },
                    { "TopP", 1 },
                }
            });
    }

    /// <summary>
    /// Calculates the result of a non-trivial math expression.
    /// </summary>
    /// <param name="input">A valid mathematical expression that could be executed by a calculator capable of more advanced math functions like sine/cosine/floor.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <returns>A <see cref="Task{TResult}"/> representing the result of the asynchronous operation.</returns>
    [KernelFunction("Calculator"), Description("Useful for getting the result of a non-trivial math expression.")]
    public async Task<string> CalculateAsync(
        [Description("A valid mathematical expression that could be executed by a calculator capable of more advanced math functions like sin/cosine/floor.")]
        string input,
        Kernel kernel)
    {
        string answer;

        try
        {
            var result = await kernel.InvokeAsync(this._mathTranslator, new() { ["input"] = input }).ConfigureAwait(false);
            answer = result?.GetValue<string>() ?? string.Empty;
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Error in calculator for input {input} {ex.Message}", ex);
        }

        string pattern = @"```\s*(.*?)\s*```";

        Match match = Regex.Match(answer, pattern, RegexOptions.Singleline);
        if (match.Success)
        {
            var result = EvaluateMathExpression(match);
            return result;
        }

        throw new InvalidOperationException($"Input value [{input}] could not be understood, received following {answer}");
    }

    private static string EvaluateMathExpression(Match match)
    {
        var textExpressions = match.Groups[1].Value;
        var expr = new Expression(textExpressions, EvaluateOptions.IgnoreCase);
        expr.EvaluateParameter += (string name, ParameterArgs args) =>
        {
            args.Result = name.ToLower(System.Globalization.CultureInfo.CurrentCulture) switch
            {
                "pi" => Math.PI,
                "e" => Math.E,
                _ => args.Result
            };
        };

        try
        {
            if (expr.HasErrors())
            {
                return "Error:" + expr.Error + " could not evaluate " + textExpressions;
            }

            var result = expr.Evaluate();
            return "Answer:" + result.ToString();
        }
        catch (Exception e)
        {
            throw new InvalidOperationException("could not evaluate " + textExpressions, e);
        }
    }
}
