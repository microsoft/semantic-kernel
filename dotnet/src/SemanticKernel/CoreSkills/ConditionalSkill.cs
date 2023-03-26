// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.ControlFlow;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.CoreSkills;
public class ConditionalSkill
{
    #region Prompts
    internal const string IfStructureCheckPrompt =
        @"Structure:
<if>
	<conditiongroup/>
	<then/>
	<else/>
</if>

Rules:
. A ""Condition Group"" must exists and have at least one ""Condition"" or ""Condition Group"" child
. Check recursively if any existing the children ""Condition Group"" follow the Rule 1
. ""Then"" must exists and have at least one child node
. ""Else"" is optional
. If ""Else"" is provided must have one or more children nodes
. Return true if Test Structure is valid
. Return false if Test Structure is not valid with a reason
. Give a json list of variables used inside all the ""Condition Group""s
. All the return should be in Json format.
. Response Json Structure:
{
  ""valid"": bool,
  ""reason"": string,
  ""variables"": [string]
}

Test Structure:
{{$IfStatementContent}}";

    internal const string EvaluateConditionPrompt =
        @"Rules
. ""and"" and ""or"" should be self closing tags

Given:
<conditiongroup>
    <condition variable=""x"" exact=""1"" />
    <and/>
    <condition variable=""y"" contains=""asd"" />
    <or/>
    <not>
        <condition variable=""z"" greaterthan=""10"" />
    </not>
</conditiongroup>

Evaluate:
(x == ""1"" ^ y.Contains(""asd"") ∨ ¬(z > 10))
(TRUE ^ TRUE ∨ ¬ (FALSE))
(TRUE ^ TRUE ∨ TRUE) = TRUE

Variables:
x = ""2""
y = ""adfsdasfgsasdddsf""
z = ""100""
w = ""sdf""

Expect: TRUE

Given:
<if>
     <conditiongroup>
          <condition variable=""24hour"" exact=""1"" />
          <and/>
          <condition variable=""24hour"" greaterthan=""10"" />
     </conditiongroup>
     <then><if>Good Morning</if></then>
     <else><else>Good afternoon</else></else>
</if>

Variables:
24hour = 11

Evaluate:
(24hour == 1 ^ 24hour > 10)
(FALSE ^ TRUE) = FALSE

Expect: FALSE

Given:
Invalid XML

Variables:
24hour = 11

Expect: ERROR
Reason: 

Given:
<conditiongroup>
<condition variable=""23hour"" exact=""10""/>
</conditiongroup>

Variables:
24hour = 11

Expect: ERROR
Reason: 23hour is not a valid variable. 

Given:
{{$IfStatementContent}}

Variables:
{{$ConditionalVariables}}

Expect: ";

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

    public ConditionalSkill(IKernel kernel, ITextCompletionClient? completionBackend = null)
    {
        this._ifStructureCheckFunction = kernel.CreateSemanticFunction(
            IfStructureCheckPrompt,
            skillName: nameof(ConditionalSkill),
            description: "Evaluate if an If structure is valid and returns TRUE or FALSE",
            maxTokens: 10,
            temperature: 0,
            stopSequences: new string[] { "\n" },
            topP: 0.5
            );

        this._evaluateConditionFunction = kernel.CreateSemanticFunction(
            EvaluateConditionPrompt,
            skillName: nameof(ConditionalSkill),
            description: "Evaluate a condition group and returns TRUE or FALSE",
            maxTokens: 40,
            temperature: 0,
            topP: 0.5);

        this._evaluateIfBranchFunction = kernel.CreateSemanticFunction(
            ExtractThenOrElseFromIfPrompt,
            skillName: nameof(ConditionalSkill),
            description: "Extract the content of the first child tag from the root If element",
            maxTokens: 10,
            temperature: 0,
            topP: 0.5);

        if (completionBackend is not null)
        {
            this._ifStructureCheckFunction.SetAIBackend(() => completionBackend);
            this._evaluateIfBranchFunction.SetAIBackend(() => completionBackend);
            this._evaluateConditionFunction.SetAIBackend(() => completionBackend);
        }
    }

    /// <summary>
    /// Get a planner if statement content and output then or else contents depending on the conditional evaluation.
    /// </summary>
    /// <param name="ifContent">If statement content.</param>
    /// <param name="context"> The context to use </param>
    /// <returns>Then or Else contents depending on the conditional evaluation</returns>
    /// <remarks>
    /// This skill is initially intended to be used only by the Plan Runner.
    /// </remarks>
    [SKFunction("Get a planner if statement content and output then or else contents depending on the conditional evaluation.")]
    public async Task<SKContext> IfAsync(string ifContent, SKContext context)
    {
        var usedVariables = await this.GetVariablesAndEnsureIfStructureIsValidAsync(ifContent, context).ConfigureAwait(false);

        bool conditionEvaluation = await this.EvaluateConditionAsync(ifContent, usedVariables, context).ConfigureAwait(false);

        return await this.GetThenOrElseBranchAsync(ifContent, conditionEvaluation, context).ConfigureAwait(false);
    }

    private async Task<SKContext> GetThenOrElseBranchAsync(string ifContent, bool trueCondition, SKContext context)
    {
        var branchVariables = new ContextVariables(ifContent);
        context.Variables.Set("EvaluateIfBranchTag", trueCondition ? "Then" : "Else");
        context.Variables.Set("IfStatementContent", ifContent);

        return (await this._evaluateIfBranchFunction.InvokeAsync(context).ConfigureAwait(false));
    }

    private async Task<IEnumerable<string>> GetVariablesAndEnsureIfStructureIsValidAsync(string statement, SKContext context)
    {
        context.Variables.Set("IfStatementContent", statement);
        var llmCheckFunctionResponse = (await this._ifStructureCheckFunction.InvokeAsync(statement, context).ConfigureAwait(false)).ToString();

        JsonNode llmResponse = this.GetValuesFromResponse(llmCheckFunctionResponse);
        var valid = llmResponse["valid"]!.GetValue<bool>();

        if (!valid)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidStatementStructure, llmResponse?["reason"]?.GetValue<string>() ?? NoReasonMessage);
        }

        return llmResponse?["variables"]?.Deserialize<string[]>()
            .Where(v => !string.IsNullOrWhiteSpace(v)) ?? Enumerable.Empty<string>();
    }

    private async Task<bool> EvaluateConditionAsync(string conditionContent, IEnumerable<string> usedVariables, SKContext context)
    {
        context.Variables.Set("IfStatementContent", conditionContent);
        context.Variables.Set("ConditionalVariables", this.GetConditionalVariablesFromContext(usedVariables, context.Variables));

        var llmConditionResponse = (await this._evaluateConditionFunction.InvokeAsync(conditionContent, context).ConfigureAwait(false)).ToString();

        var reason = this.GetReason(llmConditionResponse);
        var error = !Regex.Match(llmConditionResponse, @"^(true|false)", RegexOptions.IgnoreCase).Success;
        if (error)
        {
            throw new ConditionException(ConditionException.ErrorCodes.InvalidConditionFormat, reason);
        }

        return llmConditionResponse.StartsWith("TRUE", StringComparison.OrdinalIgnoreCase);
    }

    private string GetConditionalVariablesFromContext(IEnumerable<string> usedVariables, ContextVariables variables)
    {
        var checkNotFoundVariables = usedVariables.Where(u => !variables.ContainsKey(u));
        if (checkNotFoundVariables.Any())
        {
            throw new ConditionException(ConditionException.ErrorCodes.ContextVariablesNotFound, string.Join(", ", checkNotFoundVariables));
        }

        return string.Join("\n", variables
            .Where(v => usedVariables.Contains(v.Key))
            .Select(x => $"{x.Key} = {x.Value}"));
    }

    private string? GetReason(string llmResponse)
    {
        var hasReasonIndex = llmResponse.IndexOf(ReasonIdentifier, StringComparison.OrdinalIgnoreCase);
        if (hasReasonIndex > -1)
        {
            return llmResponse[(hasReasonIndex+ ReasonIdentifier.Length)..].Trim();
        }
        return NoReasonMessage;
    }

    private JsonNode GetValuesFromResponse(string llmResponse)
    {
        var startIndex = llmResponse.IndexOf('{', StringComparison.InvariantCultureIgnoreCase);
        JsonNode? response = null;

        if (startIndex > -1)
        {
            var jsonResponse = llmResponse[startIndex..];
            response = JsonSerializer.Deserialize<JsonNode>(jsonResponse);
        }

        if (response is not null)
        {
            return response;
        }

        throw new ConditionException(ConditionException.ErrorCodes.JsonResponseNotFound);
    }
}
