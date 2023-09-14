// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Planning.Structured.Stepwise;

using System;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Connectors.AI.OpenAI.FunctionCalling;


/// <summary>
///  A function call for use with the Stepwise Planner
/// </summary>
public class StepwiseFunctionCallResult : FunctionCallResult
{
    /// <summary>
    /// The action to take
    /// </summary>
    [JsonPropertyName("function_call")]
    public FunctionCallResult? FunctionCall { get; set; }

    /// <summary>
    /// Rationale given by the LLM for choosing the function
    /// </summary>
    [JsonPropertyName("thought")]
    public string? Thought { get; set; }

    /// <summary>
    ///  The result of the last action taken
    /// </summary>
    [JsonPropertyName("observation")]
    public string? Observation { get; set; }

    /// <summary>
    ///  The final answer to the question
    /// </summary>
    [JsonPropertyName("final_answer")]
    public string? FinalAnswer { get; set; }

    /// <summary>
    ///  The raw result of the last action taken
    /// </summary>
    [JsonPropertyName("function_result")]
    public string? FunctionResult { get; set; }


    /// <summary>
    ///  Convert the StepwiseFunctionCallResult to a formatted string
    /// </summary>
    /// <param name="step"></param>
    /// <returns></returns>
    public string ToStepResult(int step)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Step {step}:");

        if (!string.IsNullOrEmpty(Observation))
        {
            sb.AppendLine($" Observation: {Observation}");
        }

        if (!string.IsNullOrEmpty(Thought))
        {
            sb.AppendLine($" -Thought: {Thought}");
        }

        if (!string.IsNullOrEmpty(Function))
        {
            sb.AppendLine($" -Function_Call => {Function}");

            sb.AppendLine(" -Parameters:");

            foreach (var parameter in Parameters)
            {
                sb.AppendLine($"  {parameter.Name}: {parameter.Value}");
            }
        }

        if (!string.IsNullOrEmpty(FunctionResult))
        {
            sb.AppendLine($" -Function_Result: {FunctionResult}");
        }

        if (!string.IsNullOrEmpty(FinalAnswer))
        {
            sb.AppendLine($" -Final_Answer: {FinalAnswer}");
        }
        return sb.ToString();
    }


    public string GetAssistantMessage()
    {
        var stringBuilder = new StringBuilder();

        if (!string.IsNullOrEmpty(Observation))
        {
            stringBuilder.AppendLine($"{nameof(Observation)}: {Observation}");
        }

        if (!string.IsNullOrEmpty(Thought))
        {
            stringBuilder.AppendLine($"{nameof(Thought)}: {Thought}");
        }

        if (!string.IsNullOrEmpty(Function))
        {
            stringBuilder.AppendLine($"Function_Call: {JsonSerializer.Serialize(new { function_call = Function, parameters = Parameters })}");
        }

        if (!string.IsNullOrEmpty(FinalAnswer))
        {
            stringBuilder.AppendLine($"{nameof(FinalAnswer)}: {FinalAnswer}");
        }

        return stringBuilder.ToString().Trim();
    }


    /// <inheritdoc />
    public override string ToString()
    {
        var stringBuilder = new StringBuilder();

        if (!string.IsNullOrEmpty(Thought))
        {
            stringBuilder.AppendLine($"{nameof(Thought)}: {Thought}");
        }

        if (FunctionCall != null)
        {
            stringBuilder.AppendLine($"Function_Call: {JsonSerializer.Serialize(new { function_call = FunctionCall.Function, parameters = FunctionCall.Parameters })}");
        }

        if (!string.IsNullOrEmpty(Observation))
        {
            stringBuilder.AppendLine($"Observation: {Observation}");
        }

        if (!string.IsNullOrEmpty(FunctionResult))
        {
            stringBuilder.AppendLine($"{nameof(FunctionResult)}: {FunctionResult}");
        }

        if (!string.IsNullOrEmpty(FinalAnswer))
        {
            stringBuilder.AppendLine($"{nameof(FinalAnswer)}: {FinalAnswer}");
        }

        return stringBuilder.ToString().Trim();
    }


    /// <summary>
    /// Compare two StepwiseFunctionCallResults
    /// </summary>
    /// <param name="obj"></param>
    /// <returns></returns>
    public override bool Equals(object? obj)
    {
        if (obj is StepwiseFunctionCallResult other)
        {
            bool functionEquality = Function.Equals(other.Function, StringComparison.Ordinal);
            bool parametersEquality = Parameters.Equals(other.Parameters);
            bool thoughtEquality = Thought?.Equals(other.Thought, StringComparison.Ordinal) ?? other.Thought == null;
            bool observationEquality = Observation?.Equals(other.Observation, StringComparison.Ordinal) ?? other.Observation == null;
            bool resultEquality = FunctionResult?.Equals(other.FunctionResult, StringComparison.Ordinal) ?? other.FunctionResult == null;
            return functionEquality && parametersEquality && thoughtEquality && observationEquality && resultEquality;
        }

        return base.Equals(obj);
    }


    public override int GetHashCode() =>
        // Create a hash based on the Action's Function, Thought, Observation, and Parameters
        HashCode.Combine(FunctionCall?.Function, Thought, Observation, FunctionCall?.Parameters);
}
