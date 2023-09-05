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
            sb.AppendLine($" Thought: {Thought}");
        }

        if (FunctionCall != null)
        {
            sb.AppendLine($" Function_Call => {FunctionCall.Function}");

            sb.AppendLine(" Parameters:");

            foreach (var parameter in FunctionCall.Parameters)
            {
                sb.AppendLine($"  {parameter.Name}: {parameter.Value}");
            }
        }

        if (!string.IsNullOrEmpty(FunctionResult))
        {
            sb.AppendLine($" Function_Result: {FunctionResult}");
        }

        if (!string.IsNullOrEmpty(FinalAnswer))
        {
            sb.AppendLine($" Final_Answer: {FinalAnswer}");
        }
        return sb.ToString();
    }


    /// <inheritdoc />
    public override string ToString()
    {
        var stringBuilder = new StringBuilder();

        if (!string.IsNullOrEmpty(Thought))
        {
            stringBuilder.AppendLine($"[{nameof(Thought)}] {Thought}");
        }

        if (!string.IsNullOrEmpty(Observation))
        {
            stringBuilder.AppendLine($"[{nameof(Observation)}] {Observation}");
        }

        if (FunctionCall != null)
        {
            stringBuilder.AppendLine($"[{nameof(FunctionCall)}] {JsonSerializer.Serialize(new { action = FunctionCall.Function, action_variables = FunctionCall.Parameters })}");
        }

        if (!string.IsNullOrEmpty(FunctionResult))
        {
            stringBuilder.AppendLine($"[{nameof(FunctionResult)}] {FunctionResult}");
        }

        if (!string.IsNullOrEmpty(FinalAnswer))
        {
            stringBuilder.AppendLine($"[{nameof(FinalAnswer)}] {FinalAnswer}");
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
            var functionEquality = FunctionCall?.Equals(other.FunctionCall) == true;
            var thoughtEquality = Thought?.Equals(other.Thought, StringComparison.OrdinalIgnoreCase) == true;
            var observationEquality = Observation?.Equals(other.Observation, StringComparison.OrdinalIgnoreCase) == true;
            return functionEquality && thoughtEquality && observationEquality;
        }

        return base.Equals(obj);
    }


    public override int GetHashCode() =>
        // Create a hash based on the Action's Function, Thought, Observation, and Parameters
        HashCode.Combine(FunctionCall?.Function, Thought, Observation, FunctionCall?.Parameters);
}
