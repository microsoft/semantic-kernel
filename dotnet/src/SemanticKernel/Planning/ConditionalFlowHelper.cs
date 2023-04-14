// Copyright (c) Microsoft. All rights reserved.

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
    internal const string NoReasonMessage = "No reason was provided";

    private readonly ISKFunction _ifStructureCheckFunction;
    private readonly ISKFunction _evaluateConditionFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConditionalFlowHelper"/> class.
    /// </summary>
    /// <param name="kernel"> The kernel to use </param>
    /// <param name="completionBackend"> A optional completion backend to run the internal semantic functions </param>
    internal ConditionalFlowHelper(IKernel kernel, ITextCompletion? completionBackend = null)
    {
        this._ifStructureCheckFunction = kernel.CreateSemanticFunction(
            ConditionalFlowConstants.IfStructureCheckPrompt,
            skillName: "PlannerSkill_Excluded",
            description: "Evaluate if an If structure is valid and returns TRUE or FALSE",
            maxTokens: 100,
            temperature: 0,
            topP: 0.5);

        this._evaluateConditionFunction = kernel.CreateSemanticFunction(
            ConditionalFlowConstants.EvaluateConditionPrompt,
            skillName: "PlannerSkill_Excluded",
            description: "Evaluate a condition group and returns TRUE or FALSE",
            maxTokens: 100,
            temperature: 0,
            topP: 0.5);

        if (completionBackend is not null)
        {
            this._ifStructureCheckFunction.SetAIService(() => completionBackend);
            this._evaluateConditionFunction.SetAIService(() => completionBackend);
        }
    }

    /// <summary>
    /// Get a planner if statement content and output <if/> or <else/> contents depending on the conditional evaluation.
    /// </summary>
    /// <param name="ifFullContent">Full statement content including if and else.</param>
    /// <param name="context"> The context to use </param>
    /// <returns>Then or Else contents depending on the conditional evaluation</returns>
    /// <remarks>
    /// This skill is initially intended to be used only by the Plan Runner.
    /// </remarks>
    public async Task<string> IfAsync(string ifFullContent, SKContext context)
    {
        XmlDocument xmlDoc = new();
        xmlDoc.LoadXml("<xml>" + ifFullContent + "</xml>");

        this.EnsureIfStructure(xmlDoc, out var ifNode, out var elseNode);

        var usedVariables = this.GetUsedVariables(ifNode);

        // Temporarily avoiding going to LLM to resolve variable and If structure
        // await this.GetVariablesAndEnsureIfStructureIsValidAsync(ifNode.OuterXml, context).ConfigureAwait(false);

        bool conditionEvaluation = await this.EvaluateConditionAsync(ifNode, usedVariables, context).ConfigureAwait(false);

        return conditionEvaluation
            ? ifNode.InnerXml
            : elseNode?.InnerXml ?? string.Empty;
    }

    /// <summary>
    /// Get a planner while statement content and output or not its contents depending on the conditional evaluation.
    /// </summary>
    /// <param name="whileContent">While content.</param>
    /// <param name="context"> The context to use </param>
    /// <returns>None if evaluates to false or the children steps appended of a copy of the while structure</returns>
    /// <remarks>
    /// This skill is initially intended to be used only by the Plan Runner.
    /// </remarks>
    public async Task<string> WhileAsync(string whileContent, SKContext context)
    {
        XmlDocument xmlDoc = new();
        xmlDoc.LoadXml("<xml>" + whileContent + "</xml>");

        this.EnsureWhileStructure(xmlDoc, out var whileNode);

        var usedVariables = this.GetUsedVariables(whileNode);

        bool conditionEvaluation = await this.EvaluateConditionAsync(whileNode, usedVariables, context).ConfigureAwait(false);

        return conditionEvaluation
            ? whileNode.InnerXml + whileContent
            : string.Empty;
    }

    private void EnsureIfStructure(XmlDocument xmlDoc, out XmlNode ifNode, out XmlNode? elseNode)
    {
        ifNode =
            xmlDoc.SelectSingleNode("//if")
            ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "If is not present");

        XmlAttribute? conditionContents = ifNode.Attributes?["condition"];

        if (conditionContents is null)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "Condition attribute is not present");
        }

        if (string.IsNullOrWhiteSpace(conditionContents.Value))
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "Condition attribute value cannot be empty");
        }

        if (!ifNode.HasChildNodes)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "If has no children");
        }

        elseNode = xmlDoc.SelectSingleNode("//else");
        if (elseNode is not null && !elseNode.HasChildNodes)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "Else has no children");
        }
    }

    private void EnsureWhileStructure(XmlDocument xmlDoc, out XmlNode whileNode)
    {
        whileNode =
            xmlDoc.SelectSingleNode("//while")
            ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "While is not present");

        XmlAttribute? conditionContents = whileNode.Attributes?["condition"];

        if (conditionContents is null)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "Condition attribute is not present");
        }

        if (string.IsNullOrWhiteSpace(conditionContents.Value))
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "Condition attribute value cannot be empty");
        }

        if (!whileNode.HasChildNodes)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, "While has no children");
        }
    }

    /// <summary>
    /// Get the variables used in the If statement and ensure the structure is valid using LLM
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
    /// Get the variables used in the If statement condition
    /// </summary>
    /// <param name="ifNode">If Xml Node</param>
    /// <returns>List of used variables in the if node condition attribute</returns>
    /// <exception cref="ConditionException">InvalidStatementStructure</exception>
    /// <exception cref="ConditionException">InvalidCondition</exception>
    private IEnumerable<string> GetUsedVariables(XmlNode ifNode)
    {
        var foundVariables = Regex.Matches(ifNode.Attributes!["condition"].Value, "\\$[0-9A-Za-z_]+");
        if (foundVariables.Count == 0)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidCondition, "No variables found in the condition");
        }

        foreach (Match foundVariable in foundVariables)
        {
            // Return the variables without the $
            yield return foundVariable.Value.Substring(1);
        }
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

        context.Log.LogDebug("Conditional evaluation: {0}", llmJsonResponse["reason"] ?? NoReasonMessage);

        return llmJsonResponse["condition"]?.GetValue<bool>()
               ?? throw new ConditionException(ConditionException.ErrorCodes.InvalidResponse, "Condition property null or not found");
    }

    /// <summary>
    /// Extracts the condition root group content closest the If structure
    /// </summary>
    /// <param name="ifNode">If node to extract condition from</param>
    /// <returns>Condition group contents</returns>
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
        var existingVariables = variables.Where(v => usedVariables.Contains(v.Key));

        var conditionalVariables = new StringBuilder();
        foreach (var v in existingVariables)
        {
            // Numeric don't add quotes
            var value = Regex.IsMatch(v.Value, "^[0-9.,]+$") ? v.Value : JsonSerializer.Serialize(v.Value);
            conditionalVariables.AppendLine($"{v.Key} = {value}");
        }

        foreach (string notFoundVariable in checkNotFoundVariables)
        {
            conditionalVariables.AppendLine($"{notFoundVariable} = undefined");
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
        var startIndex = llmResponse?.IndexOf('{') ?? -1;
        JsonNode? response = null;

        if (startIndex > -1)
        {
            var jsonResponse = llmResponse!.Substring(startIndex);
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
