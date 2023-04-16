// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning;

internal class ConditionalFlowConstants
{
    internal const string IfStructureCheckPrompt =
        @"Structure:
<if condition="""">
</if>
<else> (optional)
</else>

Rules:
. A condition attribute must exists in the if tag
. ""if"" tag must have one or more children nodes
. ""else"" tag is optional
. If ""else"" is provided must have one or more children nodes
. Return true if Test Structure is valid
. Return false if Test Structure is not valid with a reason with everything that is wrong
. Give a json list of variables used inside the attribute ""condition"" of the first ""if"" only
. All the return should be in Json format.
. Response Json Structure:
{
    ""valid"": bool,
    ""reason"": string, (only if invalid)
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
}
