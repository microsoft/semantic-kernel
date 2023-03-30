// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Xml;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// <para>Semantic skill that evaluates conditional structures</para>
/// <para>
/// Usage:
/// var kernel = SemanticKernel.Build(ConsoleLogger.Log);
/// kernel.ImportSkill("conditional", new ConditionalSkill(kernel));
/// </para>
/// </summary>
public class ConditionalFlowHelper
{
    private readonly IKernel _kernel;

    #region Prompts

    internal const string IfStructureCheckPrompt =
        @"Structure:
<if condition="""">
</if>
<else>
</else>

Rules:
. A condition attribute must exists in the if tag
. ""If"" tag must have one or more children nodes
. ""Else"" is optional
. If ""Else"" is provided must have one or more children nodes
. Return true if Test Structure is valid
. Return false if Test Structure is not valid with a reason with everything that is wrong
. Give a json list of variables used inside the attribute ""condition"" of the first ""IF"" only
. All the return should be in Json format.
. Response Json Structure:
{
    ""valid"": bool,
    ""reason"": string,
    ""variables"": [string] (only the variables within ""Condition"" attribute)
}

Test Structure:
{{$IfStatementContent}}

Response: ";

    internal const string EvaluateConditionPrompt =
        @"Rules
. Response using the following json structure:
{ ""valid"": bool, ""condition"": bool, ""reason"": string }

. A list of variables will be provided for the condition evaluation
. If condition has an error, valid will be false and property ""reason"" will have all detail why.
. If condition is valid, update reason with the current evaluation detail.
. Return ""condition"" as true or false depending on the condition evaluation

Variables Example:
x = 2
y = ""adfsdasfgsasdddsf""
z = 100
w = ""sdf""

Given Example:
$x equals 1 and $y contains 'asd' or not ($z greaterthan 10)

Reason Example:
(x == 1 ∧ (y contains ""asd"") ∨ ¬(z > 10))
(TRUE ∧ TRUE ∨ ¬ (FALSE))
(TRUE ∧ TRUE ∨ TRUE)
TRUE

Variables Example:
24hour = 11

Given Example:
$24hour equals 1 and $24hour greaterthan 10

Response Example:
{ ""valid"": true, ""condition"": false, ""reason"": ""(24hour == 1 ∧ 24hour > 10) = (FALSE ∧ TRUE) = FALSE"" }

Variables Example:
24hour = 11

Given Example:
Some condition

Response Example:
{ ""valid"": false, ""reason"": ""<detail why>"" }

Variables Example:
a = 1
b = undefined
c = ""dome""

Given Example:
(a is not undefined) and a greaterthan 100 and a greaterthan 10 or (a equals 1 and a equals 10) or (b is undefined and c is not undefined)

Response Example:
{ ""valid"": true, ""condition"": true, ""reason"": ""((a is not undefined) ∧ a > 100 ∧ a > 10) ∨ (a == 1 ∧ a == 10) ∨ (b is undefined ∧ c is not undefined) = ((TRUE ∧ FALSE ∧ FALSE) ∨ (TRUE ∧ FALSE) ∨ (TRUE ∧ TRUE)) = (FALSE ∨ FALSE ∨ TRUE) = TRUE"" }

Variables:
{{$ConditionalVariables}}

Given:
{{$IfCondition}}

Response: ";

    internal const string ExtractThenOrElseFromIfPrompt =
        @"Consider the below structure, ignore any format error:

{{$IfStatementContent}}

Rules:
Don't ignore non xml 
Invalid XML is part of the content

Now, write the exact content inside the first child ""{{$EvaluateIfBranchTag}}"" from the root If element

The exact content inside the first child ""{{$EvaluateIfBranchTag}}"" element from the root If element is:

";

    #endregion

    internal const string ReasonIdentifier = "Reason:";
    internal const string NoReasonMessage = "No reason was provided";

    private readonly ISKFunction _ifStructureCheckFunction;
    private readonly ISKFunction _evaluateConditionFunction;
    private readonly ISKFunction _evaluateIfBranchFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConditionalFlowHelper"/> class.
    /// </summary>
    /// <param name="kernel"> The kernel to use </param>
    /// <param name="completionBackend"> A optional completion backend to run the internal semantic functions </param>
    internal ConditionalFlowHelper(IKernel kernel, ITextCompletion? completionBackend = null)
    {
        this._kernel = kernel;
        this._ifStructureCheckFunction = kernel.CreateSemanticFunction(
            IfStructureCheckPrompt,
            skillName: "PlannerSkill_Excluded",
            description: "Evaluate if an If structure is valid and returns TRUE or FALSE",
            maxTokens: 100,
            temperature: 0,
            topP: 0.5);

        this._evaluateConditionFunction = kernel.CreateSemanticFunction(
            EvaluateConditionPrompt,
            skillName: "PlannerSkill_Excluded",
            description: "Evaluate a condition group and returns TRUE or FALSE",
            maxTokens: 100,
            temperature: 0,
            topP: 0.5);

        this._evaluateIfBranchFunction = kernel.CreateSemanticFunction(
            ExtractThenOrElseFromIfPrompt,
            skillName: "PlannerSkill_Excluded",
            description: "Extract the content of the first child tag from the root If element",
            maxTokens: 1000,
            temperature: 0,
            topP: 0.5);

        if (completionBackend is not null)
        {
            this._ifStructureCheckFunction.SetAIService(() => completionBackend);
            this._evaluateIfBranchFunction.SetAIService(() => completionBackend);
            this._evaluateConditionFunction.SetAIService(() => completionBackend);
        }
    }

    /// <summary>
    /// Get a planner if statement content and output then or else contents depending on the conditional evaluation.
    /// </summary>
    /// <param name="ifFullContent">If statement content.</param>
    /// <param name="context"> The context to use </param>
    /// <returns>Then or Else contents depending on the conditional evaluation</returns>
    /// <remarks>
    /// This skill is initially intended to be used only by the Plan Runner.
    /// </remarks>
    public async Task<string> IfAsync(string ifFullContent, SKContext context)
    {
        XmlDocument xmlDoc = new();
        xmlDoc.LoadXml("<xml>" + ifFullContent + "</xml>");

        XmlNode ifNode =
            xmlDoc.SelectSingleNode("//if")
            ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "If is not present");

        XmlNode? elseNode = xmlDoc.SelectSingleNode("//else");

        var usedVariables = await this.GetVariablesAndEnsureIfStructureIsValidAsync(ifNode.OuterXml, context).ConfigureAwait(false);

        bool conditionEvaluation = await this.EvaluateConditionAsync(ifNode, usedVariables, context).ConfigureAwait(false);

        return conditionEvaluation
            ? ifNode.InnerXml
            : elseNode?.InnerXml ?? string.Empty;
    }

    /// <summary>
    /// Get the variables used in the If statement and ensure the structure is valid
    /// </summary>
    /// <param name="ifContent">If structure content</param>
    /// <param name="context">Current context</param>
    /// <returns>List of used variables in the if condition</returns>
    /// <exception cref="ConditionException">InvalidStatementStructure</exception>
    /// <exception cref="ConditionException">InvalidResponse</exception>
    private async Task<IEnumerable<string>> GetVariablesAndEnsureIfStructureIsValidAsync(string ifContent, SKContext context)
    {
        context.Variables.Set("IfStatementContent", ifContent);
        var llmRawResponse = (await this._ifStructureCheckFunction.InvokeAsync(ifContent, context).ConfigureAwait(false)).ToString();

        JsonNode llmJsonResponse = this.GetLlmResponseAsJsonWithProperties(llmRawResponse, "valid");
        var valid = llmJsonResponse["valid"]!.GetValue<bool>();

        if (!valid)
        {
            var reason = llmJsonResponse?["reason"]?.GetValue<string>();

            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure,
                !string.IsNullOrWhiteSpace(reason)
                    ? reason
                    : NoReasonMessage);
        }

        // Get all variables from the json array and remove the $ prefix, return empty list if no variables are found
        var usedVariables = llmJsonResponse["variables"]?.Deserialize<string[]>()?
                                .Where(v => !string.IsNullOrWhiteSpace(v))
                                .Select(v => v.TrimStart('$'))
                            ?? Enumerable.Empty<string>();

        return usedVariables;
    }

    /// <summary>
    /// Evaluates a condition group and returns TRUE or FALSE
    /// </summary>
    /// <param name="ifNode">If structure content</param>
    /// <param name="usedVariables">Used variables to send for evaluation</param>
    /// <param name="context">Current context</param>
    /// <returns>Condition result</returns>
    /// <exception cref="ConditionException">InvalidCondition</exception>
    /// <exception cref="ConditionException">ContextVariablesNotFound</exception>
    private async Task<bool> EvaluateConditionAsync(XmlNode ifNode, IEnumerable<string> usedVariables, SKContext context)
    {
        var conditionContent = this.ExtractConditionalContent(ifNode);

        context.Variables.Set("IfCondition", conditionContent);
        context.Variables.Set("ConditionalVariables", this.GetConditionalVariablesFromContext(usedVariables, context.Variables));

        var llmRawResponse =
            (await this._evaluateConditionFunction.InvokeAsync(conditionContent, context).ConfigureAwait(false))
            .ToString();

        JsonNode llmJsonResponse = this.GetLlmResponseAsJsonWithProperties(llmRawResponse, "valid");

        if (llmJsonResponse is null)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidResponse, "Response is null");
        }

        var valid = llmJsonResponse["valid"]!.GetValue<bool>();
        var reason = llmJsonResponse["reason"]?.GetValue<string>();

        if (!valid)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidCondition,
                !string.IsNullOrWhiteSpace(reason)
                    ? reason
                    : NoReasonMessage);
        }

        context.Log.LogWarning("Conditional evaluation: {0}", llmJsonResponse["reason"] ?? NoReasonMessage);

        return llmJsonResponse["condition"]?.GetValue<bool>()
               ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidResponse, "Condition property null or not found");
    }

    /// <summary>
    /// Extracts the condition root group content closest the If structure
    /// </summary>
    /// <param name="ifNode">If node to extract condition from</param>
    /// <returns>Conditiongroup contents</returns>
    private string ExtractConditionalContent(XmlNode ifNode)
    {
        var conditionContent = ifNode.Attributes?["condition"]
                               ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidCondition, "<if> has no condition attribute");

        return conditionContent.Value;
    }

    /// <summary>
    /// Gets all the variables used in the condition and their values from the context
    /// </summary>
    /// <param name="usedVariables">Variables used in the condition</param>
    /// <param name="variables">Context variables</param>
    /// <returns>List of variables and its values for prompting</returns>
    /// <exception cref="ConditionException">ContextVariablesNotFound</exception>
    private string GetConditionalVariablesFromContext(IEnumerable<string> usedVariables, ContextVariables variables)
    {
        var checkNotFoundVariables = usedVariables.Where(u => !variables.ContainsKey(u)).ToArray();
        if (checkNotFoundVariables.Any())
        {
            throw new ConditionException(ConditionException.ErrorCodes.ContextVariablesNotFound, string.Join(", ", checkNotFoundVariables));
        }

        var existingVariables = variables.Where(v => usedVariables.Contains(v.Key));

        var conditionalVariables = new StringBuilder();
        foreach (var v in existingVariables)
        {
            // Numeric don't add quotes
            var value = Regex.IsMatch(v.Value, "^[0-9.,]+$") ? v.Value : JsonSerializer.Serialize(v.Value);
            conditionalVariables.AppendLine($"{v.Key} = {value}");
        }

        return conditionalVariables.ToString();
    }

    /// <summary>
    /// Gets a JsonNode traversable structure from the LLM text response
    /// </summary>
    /// <param name="llmResponse">String to parse into a JsonNode format</param>
    /// <param name="requiredProperties">If provided ensures if the json object has the properties</param>
    /// <returns>JsonNode with the parseable json form the llmResponse string</returns>
    /// <exception cref="ConditionException">Throws if cannot find a Json result or any of the required properties</exception>
    private JsonNode GetLlmResponseAsJsonWithProperties(string llmResponse, params string[] requiredProperties)
    {
        var startIndex = llmResponse?.IndexOf('{', StringComparison.InvariantCultureIgnoreCase) ?? -1;
        JsonNode? response = null;

        if (startIndex > -1)
        {
            var jsonResponse = llmResponse![startIndex..];
            response = JsonSerializer.Deserialize<JsonNode>(jsonResponse);

            foreach (string requiredProperty in requiredProperties)
            {
                _ = response?[requiredProperty]
                    ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidResponse,
                        $"Response doesn't have the required property: {requiredProperty}");
            }
        }

        if (response is null)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidResponse);
        }

        return response;
    }
}
