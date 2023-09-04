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
public class StepFunctionCall : FunctionCallResult
{
    /// <summary>
    /// The action to take
    /// </summary>
    [JsonPropertyName("action")]
    public FunctionCallResult? Action { get; set; }

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
    [JsonPropertyName("action_result")]
    public string? ActionResult { get; set; }


    public string ToFormattedString(string? propertyName = null)
    {
        if (string.IsNullOrEmpty(propertyName))
        {
            return ToString();
        }

        if (propertyName!.Equals(nameof(Thought), StringComparison.OrdinalIgnoreCase))
        {
            return $"[{nameof(Thought)}] {Thought}".Trim();
        }

        if (propertyName.Equals(nameof(Observation), StringComparison.OrdinalIgnoreCase))
        {
            return $"[{nameof(Observation)}] {Observation}".Trim();
        }

        if (propertyName.Equals(nameof(Action), StringComparison.OrdinalIgnoreCase))
        {
            return $"[{nameof(Action)}] {JsonSerializer.Serialize(new { action = Action?.Function, action_variables = Action?.Parameters })}".Trim();
        }

        if (propertyName.Equals(nameof(ActionResult), StringComparison.OrdinalIgnoreCase))
        {
            return $"[{nameof(ActionResult)}] {ActionResult}".Trim();
        }

        if (propertyName.Equals(nameof(FinalAnswer), StringComparison.OrdinalIgnoreCase))
        {
            return $"[{nameof(FinalAnswer)}] {FinalAnswer}".Trim();
        }

        return string.Empty;

    }


    public string ToResult(int step)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"Step {step}:");
        sb.AppendLine($"Function => {Action?.Function}");

        if (Action?.Parameters != null)
        {
            sb.AppendLine("Parameters: ");

            foreach (var parameter in Action.Parameters)
            {
                sb.AppendLine($"  {parameter.Name}: {parameter.Value}");
            }
        }
        sb.AppendLine($"Result: {ActionResult}");
        sb.AppendLine($"Observation: {Observation}");
        sb.AppendLine($"Thought: {Thought}");
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

        if (Action != null)
        {
            stringBuilder.AppendLine($"[{nameof(Action)}] {JsonSerializer.Serialize(new { action = Action.Function, action_variables = Action.Parameters })}");
        }

        if (!string.IsNullOrEmpty(ActionResult))
        {
            stringBuilder.AppendLine($"[{nameof(ActionResult)}] {ActionResult}");
        }

        if (!string.IsNullOrEmpty(FinalAnswer))
        {
            stringBuilder.AppendLine($"[{nameof(FinalAnswer)}] {FinalAnswer}");
        }

        return stringBuilder.ToString().Trim();
    }


    public override bool Equals(object? obj)
    {
        if (obj is StepFunctionCall other)
        {
            var functionEquality = Action?.Equals(other.Action) == true;
            var thoughtEquality = Thought?.Equals(other.Thought, StringComparison.OrdinalIgnoreCase) == true;
            var observationEquality = Observation?.Equals(other.Observation, StringComparison.OrdinalIgnoreCase) == true;
            return functionEquality && thoughtEquality && observationEquality;
        }

        return base.Equals(obj);
    }


    public override int GetHashCode() =>
        // Create a hash based on the Action's Function, Thought, Observation, and Parameters
        HashCode.Combine(Action?.Function, Thought, Observation, Action?.Parameters);
}
