using System.Text.RegularExpressions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using NCalc;

namespace Planning.IterativePlanner;

// usage :
    //var kernel = new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();
    //var question = "what is the square root of 625";
    //IDictionary<string, ISKFunction> calculatorSkill = kernel.ImportSkill(new LanguageCalculatorSkill(kernel));
    //SKContext summary = await kernel.RunAsync(questions, calculatorSkill["Calculate"]);
    //Console.WriteLine("Result :");
    //Console.WriteLine(summary.Result);

    public class LanguageCalculatorSkill
{
    private readonly ISKFunction _mathTranslator;

    private const string MathTranslatorPrompt =
        @"Translate a math problem into a expression that can be executed using .net NCalc library. Use the output of running this code to answer the question.

Question: $((Question with math problem.))
expression:``` $((single line mathematical expression that solves the ))``` 

[Examples]
Question: What is 37593 * 67?
expression:```37593 * 67```

Question: what is  3 to the 2nd  power?
expression:```Pow(3, 2)```

Question: what is  sinus of 0 radians?
expression:```Sin(0)```

Question: what is  sinus of 45 degrees?
expression:```Sin(45 * Pi /180 )```

Question: how many radians is 45 degrees?
expression:``` 45 * Pi / 180 ```

Question: what  is t square root of 81?
expression:```Sqrt(81)```

Question: what is the angle whose sine is the 1 number?
expression:```Asin(1)```

[End of Examples]

Question: {{ $input }}.
";

    private const string ToolDescription = "Useful for when you need to answer questions about math.";

    public LanguageCalculatorSkill(IKernel kernel)
    {
        //A skill that enables the comprehension of mathematical problems presented in English / natural-language text, followed by the execution of the necessary calculations to solve those problems.
        this._mathTranslator = kernel.CreateSemanticFunction(
            MathTranslatorPrompt,
            skillName: nameof(LanguageCalculatorSkill),
            description: ToolDescription,
            maxTokens: 50,
            temperature: 0.0,
            topP: 1);
    }

    [SKFunction(ToolDescription)]
    [SKFunctionName("Calculator")]
    public async Task<String> CalculateAsync(string input, SKContext context)
    {
        var answer = await this._mathTranslator.InvokeAsync(input).ConfigureAwait(false);
        //Console.WriteLine(answer.Result);

        string pattern = @"```\s*(.*?)\s*```";

        Match match = Regex.Match(answer.Result, pattern, RegexOptions.Singleline);
        if (match.Success)
        {
            var result = EvaluateMathExpression(match);
            return result;
        }
        else
        {
            Console.WriteLine(input);
            var e = new ArgumentException(
                $"Input value [{input}] could not be understood, received following {answer.Result} ", nameof(input));
            return await Task.FromException<string>(e).ConfigureAwait(false);
        }
    }

    private static string EvaluateMathExpression(Match match)
    {
        var textExpressions = match.Groups[1].Value;
        var expr = new Expression(textExpressions, EvaluateOptions.IgnoreCase);
        expr.EvaluateParameter += delegate(string name, ParameterArgs args)
        {
            args.Result = name.ToLower() switch
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
            throw new ApplicationException("could not evaluate " + textExpressions, e);
        }
    }
}
