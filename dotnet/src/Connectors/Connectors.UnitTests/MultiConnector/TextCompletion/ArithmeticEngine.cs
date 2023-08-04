using System;
using System.Globalization;
using System.Text.RegularExpressions;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class ArithmeticEngine
{
    public Func<ArithmeticOperation, int, int, int> ComputeFunc { get; set; } = Compute;

    public static int Compute(ArithmeticOperation operation, int operand1, int operand2)
    {
        return operation switch
        {
            ArithmeticOperation.Add => operand1 + operand2,
            ArithmeticOperation.Subtract => operand1 - operand2,
            ArithmeticOperation.Multiply => operand1 * operand2,
            ArithmeticOperation.Divide => operand1 / operand2,
            _ => throw new ArgumentOutOfRangeException(nameof(operation))
        };
    }

    public static string GeneratePrompt(ArithmeticOperation operation, int operand1, int operand2)
    {
        return $"Compute {operation}({operand1.ToString(CultureInfo.InvariantCulture)}, {operand2.ToString(CultureInfo.InvariantCulture)})";
    }

    public static (ArithmeticOperation operation, int operand1, int operand2) ParsePrompt(string prompt)
    {
        var match = Regex.Match(prompt, @"Compute (?<operation>.*)\((?<operand1>\d+), (?<operand2>\d+)\)");

        if (!match.Success)
        {
            throw new ArgumentException("Invalid prompt format.", nameof(prompt));
        }

        var operation = Enum.Parse<ArithmeticOperation>(match.Groups["operation"].Value);
        var operand1 = int.Parse(match.Groups["operand1"].Value, CultureInfo.InvariantCulture);
        var operand2 = int.Parse(match.Groups["operand2"].Value, CultureInfo.InvariantCulture);

        return (operation, operand1, operand2);
    }

    public string Run(string prompt)
    {
        var operation = ParsePrompt(prompt);
        return $"{this.ComputeFunc(operation.operation, operation.operand1, operation.operand2).ToString(CultureInfo.InvariantCulture)}";
    }
}