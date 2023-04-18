// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.CoreSkills;

internal static class SemanticFunctionConstants
{
    internal const string FunctionFlowFunctionDefinition =
        @"Create an XML plan step by step, to satisfy the goal given.
To create a plan, follow these steps:
0. The plan should be as short as possible.
1. From a <goal> create a <plan> as a series of <functions>.
2. Before using any function in a plan, check that it is present in the most recent [AVAILABLE FUNCTIONS] list. If it is not, do not use it. Do not assume that any function that was previously defined or used in another plan or in [EXAMPLES] is automatically available or compatible with the current plan.
3. Only use functions that are required for the given goal.
4. A function has an 'input' and an 'output'.
5. The 'output' from each function is automatically passed as 'input' to the subsequent <function>.
6. 'input' does not need to be specified if it consumes the 'output' of the previous function.
7. To save an 'output' from a <function>, to pass into a future <function>, use <function.{FunctionName} ... setContextVariable: ""$<UNIQUE_VARIABLE_KEY>""/>
8. To save an 'output' from a <function>, to return as part of a plan result, use <function.{FunctionName} ... appendToResult: ""RESULT__$<UNIQUE_RESULT_KEY>""/>
9. Append an ""END"" XML comment at the end of the plan.

[EXAMPLES]
[AVAILABLE FUNCTIONS]

  _GLOBAL_FUNCTIONS_.BucketOutputs:
    description: When the output of a function is too big, parse the output into a number of buckets.
    inputs:
    - input: The output from a function that needs to be parse into buckets.
    - bucketCount: The number of buckets.
    - bucketLabelPrefix: The target label prefix for the resulting buckets. Result will have index appended e.g. bucketLabelPrefix='Result' => Result_1, Result_2, Result_3

  EmailConnector.LookupContactEmail:
    description: looks up the a contact and retrieves their email address
    inputs:
    - input: the name to look up

  EmailConnector.EmailTo:
    description: email the input text to a recipient
    inputs:
    - input: the text to email
    - recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

  LanguageHelpers.TranslateTo:
    description: translate the input to another language
    inputs:
    - input: the text to translate
    - translate_to_language: the language to translate to

  WriterSkill.Summarize:
    description: summarize input text
    inputs:
    - input: the text to summarize

[END AVAILABLE FUNCTIONS]

<goal>Summarize the input, then translate to japanese and email it to Martin</goal>
<plan>
  <function.WriterSkill.Summarize/>
  <function.LanguageHelpers.TranslateTo translate_to_language=""Japanese"" setContextVariable=""TRANSLATED_TEXT"" />
  <function.EmailConnector.LookupContactEmail input=""Martin"" setContextVariable=""CONTACT_RESULT"" />
  <function.EmailConnector.EmailTo input=""$TRANSLATED_TEXT"" recipient=""$CONTACT_RESULT""/>
</plan><!-- END -->

[AVAILABLE FUNCTIONS]

  _GLOBAL_FUNCTIONS_.BucketOutputs:
    description: When the output of a function is too big, parse the output into a number of buckets.
    inputs:
    - input: The output from a function that needs to be parse into buckets.
    - bucketCount: The number of buckets.
    - bucketLabelPrefix: The target label prefix for the resulting buckets. Result will have index appended e.g. bucketLabelPrefix='Result' => Result_1, Result_2, Result_3

  _GLOBAL_FUNCTIONS_.GetEmailAddress:
    description: Gets email address for given contact
    inputs:
    - input: the name to look up

  _GLOBAL_FUNCTIONS_.SendEmail:
    description: email the input text to a recipient
    inputs:
    - input: the text to email
    - recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

  AuthorAbility.Summarize:
    description: summarizes the input text
    inputs:
    - input: the text to summarize

  Magician.TranslateTo:
    description: translate the input to another language
    inputs:
    - input: the text to translate
    - translate_to_language: the language to translate to

[END AVAILABLE FUNCTIONS]

<goal>Summarize an input, translate to french, and e-mail to John Doe</goal>
<plan>
    <function.AuthorAbility.Summarize/>
    <function.Magician.TranslateTo translate_to_language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function._GLOBAL_FUNCTIONS_.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function._GLOBAL_FUNCTIONS_.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan><!-- END -->

[AVAILABLE FUNCTIONS]

  _GLOBAL_FUNCTIONS_.BucketOutputs:
    description: When the output of a function is too big, parse the output into a number of buckets.
    inputs:
    - input: The output from a function that needs to be parse into buckets.
    - bucketCount: The number of buckets.
    - bucketLabelPrefix: The target label prefix for the resulting buckets. Result will have index appended e.g. bucketLabelPrefix='Result' => Result_1, Result_2, Result_3

  _GLOBAL_FUNCTIONS_.NovelOutline :
    description: Outlines the input text as if it were a novel
    inputs:
    - input: the title of the novel to outline
    - chapterCount: the number of chapters to outline

  Emailer.EmailTo:
    description: email the input text to a recipient
    inputs:
    - input: the text to email
    - recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

  Everything.Summarize:
    description: summarize input text
    inputs:
    - input: the text to summarize

[END AVAILABLE FUNCTIONS]

<goal>Create an outline for a children's book with 3 chapters about a group of kids in a club and then summarize it.</goal>
<plan>
  <function._GLOBAL_FUNCTIONS_.NovelOutline input=""A group of kids in a club called 'The Thinking Caps' that solve mysteries and puzzles using their creativity and logic."" chapterCount=""3"" />
  <function.Everything.Summarize/>
</plan><!-- END -->

[END EXAMPLES]

[AVAILABLE FUNCTIONS]

{{$available_functions}}

[END AVAILABLE FUNCTIONS]

<goal>{{$input}}</goal>
";

    internal const string ConditionalFunctionFlowFunctionDefinition =
        @"[PLAN 1]
  AuthorAbility.Summarize:
    description: summarizes the input text
    inputs:
    - input: the text to summarize
  Magician.TranslateTo:
    description: translate the input to another language
    inputs:
    - input: the text to translate
    - translate_to_language: the language to translate to
  _GLOBAL_FUNCTIONS_.GetEmailAddress:
    description: Gets email address for given contact
    inputs:
    - input: the name to look up
  _GLOBAL_FUNCTIONS_.SendEmail:
    description: email the input text to a recipient
    inputs:
    - input: the text to email
    - recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.

<goal>Summarize an input, translate to french, and e-mail to John Doe</goal>
<plan>
    <function.AuthorAbility.Summarize/>
    <function.Magician.TranslateTo translate_to_language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function._GLOBAL_FUNCTIONS_.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function._GLOBAL_FUNCTIONS_.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan><!-- END -->

[PLAN 2]
  Everything.Summarize:
    description: summarize input text
    inputs:
    - input: the text to summarize
  _GLOBAL_FUNCTIONS_.NovelOutline :
    description: Outlines the input text as if it were a novel
    inputs:
    - input: the title of the novel to outline
    - chapterCount: the number of chapters to outline
  LanguageHelpers.TranslateTo:
    description: translate the input to another language
    inputs:
    - input: the text to translate
    - translate_to_language: the language to translate to
  EmailConnector.LookupContactEmail:
    description: looks up the a contact and retrieves their email address
    inputs:
    - input: the name to look up
  EmailConnector.EmailTo:
    description: email the input text to a recipient
    inputs:
    - input: the text to email
    - recipient: the recipient's email address. Multiple addresses may be included if separated by ';'.
  _GLOBAL_FUNCTIONS_.Length:
    description: Get the length of a string.
    inputs:
    - input: Input string
 _GLOBAL_FUNCTIONS_.Hour:
    description: Get the current clock hour
    inputs:

<goal>If its afternoon please Summarize the input, if the input length > 10 and contains ""book"" then Create an outline for a children's book with 3 chapters about a group of kids in a club and summarize it otherwise translate to japanese and email it to Martin.</goal>
<plan>
  <function._GLOBAL_FUNCTIONS_.Hour setContextVariable=""HOUR_NUMBER""/>
  <if condition=""$HOUR_NUMBER greaterthan 12 OR $HOUR_NUMBER equals 12"">
    <function.Everything.Summarize setContextVariable=""SUMMARIZED_INPUT""/>
    <function._GLOBAL_FUNCTIONS_.Length setContextVariable=""SUMMARIZED_INPUT_LENGTH""/>
    <if condition=""$SUMMARIZED_INPUT_LENGTH greaterthan 10 and $SUMMARIZED_INPUT contains 'book'"">
        <function._GLOBAL_FUNCTIONS_.NovelOutline input=""A group of kids in a club called 'The Thinking Caps' that solve mysteries and puzzles using their creativity and logic."" chapterCount=""3"" />
       <function.Everything.Summarize/>
    </if>
    <else> (dont use elseif)
        <function.LanguageHelpers.TranslateTo input=""$SUMMARIZED_INPUT"" translate_to_language=""Japanese"" setContextVariable=""TRANSLATED_TEXT"" />
        <function.EmailConnector.LookupContactEmail input=""Martin"" setContextVariable=""CONTACT_RESULT"" />
        <function.EmailConnector.EmailTo input=""$TRANSLATED_TEXT"" recipient=""$CONTACT_RESULT""/>
    </else>
  </if>
</plan><!-- END -->

[PLAN 3]
{{$available_functions}}

Plan Rules:
Create an XML plan step by step, to satisfy the goal given.
To create a plan, follow these steps:
1. From a <goal> create a <plan> as a series of <functions>.
2. Only use functions that are required for the given goal.
3. A function has an 'input' and an 'output'.
4. The 'output' from each function is automatically passed as 'input' to the subsequent <function>.
5. 'input' does not need to be specified if it consumes the 'output' of the previous function.
6. To save an 'output' from a <function>, to pass into a future <function>, use <function.{FunctionName} ... setContextVariable: ""<UNIQUE_VARIABLE_KEY>""/>
7. To save an 'output' from a <function>, to return as part of a plan result, use <function.{FunctionName} ... appendToResult: ""RESULT__$<UNIQUE_RESULT_KEY>""/>
8. Only use ""if"", ""else"" or ""while"" tags when needed
9. ""if"", ""else"" and ""while"" tags must be closed
10. Do not use <elseif>. For such a condition, use an additional <if>...</if> block instead of <elseif>.
11. Comparison operators must be literals.
12. Append an ""END"" XML comment at the end of the plan.
13. Dont use arrays or objects for variables
14. Only use variables that where assigned before with setContextVariables
15. Use only the AVAILABLE FUNCTIONS in the deck

<goal>{{$input}}</goal>
";

    internal const string BucketFunctionDefinition =
        @"1. Given an output of a function, bucket the output into a list of results.

Examples:
[CONTENT]
Result 1
This is the first result.
Result 2
This is the second result. It's doubled!
Result 3
This is the third and final result. Truly astonishing.
[END CONTENT]

EXPECTED BUCKETS:

Result:
{""buckets"": [""Result 1
This is the first result."", ""Result 2
This is the second result. It's doubled!"", ""Result 3
This is the third and final result. Truly astonishing.""]}

End examples.

[CONTENT]
{{$input}}
[END CONTENT]

EXPECTED BUCKETS: {{$bucketCount}}

Result:
";

    internal const string ProblemSolverFunctionDefinition =
        @"Create a plan as a list, step by step, to answer the request or goal given.
To create a plan, follow these steps:
1. Identify the request or goal to be achieved.
2. Break down the request into smaller tasks and steps.
3. If the goal has a ""use"" parameter, use those functions with the exact name given.
4. Use experience and logic to determine the steps and tasks needed.
5. Provide a detailed decision-making process for each step.
6. Avoid generic instructions and add as many details as possible.
7. Present the solution using precise XML syntax with ""solution"" and ""step"" tags.
8. Ensure that all tags are closed.
9. Append an ""END"" comment at the end of the plan.
10. If you don't know how to fulfill a request, use the ""noSolution"" tag.
11. Use a computer, browser, apps, and external services to fulfill the goal.
12. Ensure that all goals are fulfilled from a computer.

Here some good examples:

<goal>
what time is it?
</goal>
<variables />
<solution>
  <step>Get current location</step>
  <step>Find the time zone for the location in the variables</step>
  <step>Get the current time for the time zone in the variables</step>
</plan><!-- END -->

<goal use=""time.timezone"">
what time is it?
</goal>
<variables />
<solution>
  <callFunction name=""time.timezone"" />
  <step>Get the current time for time zone in the variables</step>
</solution><!-- END -->

<goal use=""time.timezone,time.currentTime"">
what time is it?
</goal>
<variables />
<solution>
  <callFunction name=""time.timezone"" />
  <callFunction name=""time.currentTime"" />
  <step>Get the current time from the variables</step>
</solution><!-- END -->

<goal use=""timeSkill.GetTimezone,timeSkill.currentTime,timeSkill.currentDate"">
how long till Christmas?
</goal>
<variables />
<solution>
  <callFunction name=""timeSKill.GetTimezone"" />
  <callFunction name=""timeSKill.currentTime"" />
  <callFunction name=""timeSKill.currentDate"" />
  <step>Get the current date from the variables</step>
  <step>Calculate days from ""current date"" to ""December 25""</step>
</solution><!-- END -->

<goal>
Get user's location
</goal>
<variables />
<solution>
  <step>Search for the user location in variables</step>
  <step>If the user location is unknown ask the user: What is your location?</step>
</solution><!-- END -->

<goal use=""geo.location"">
Get user's location
</goal>
<variables />
<solution>
  <callFunction name=""geo.location"" />
  <step>Get the location from the variables</step>
  <step>If the user location is unknown ask the user to teach you how to find the value</step>
</solution><!-- END -->

<goal use=""GeoSkill.UseMyLocation"">
Find my time zone
</goal>
<variables />
<solution>
  <callFunction name=""GeoSkill.UseMyLocation"" />
  <step>Get the location from the variables</step>
  <step>If the user location is unknown ask the user: What is your location?</step>
  <step>Find the timezone for given location</step>
  <step>If the user timezone is unknown ask the user to teach you how to find the value</step>
</solution><!-- END -->

<goal>
summarize last week emails
</goal>
<variables />
<solution>
  <step>Find the current time and date</step>
  <step>Get all emails from given time to time minus 7 days</step>
  <step>Summarize the email in variables</step>
</solution><!-- END -->

<goal>
Get the current date and time
</goal>
<variables />
<solution>
  <step>Find the current date and time</step>
  <step>Get date and time from the variables</step>
</solution><!-- END -->

<goal use=""time.currentDate,time.currentTime,.GETTIMEZONE,me.myFirstName"">
Get the current date and time
</goal>
<variables />
<solution>
  <callFunction name=""time.currentDate"" />
  <callFunction name=""time.currentTime"" />
  <callFunction name="".GETTIMEZONE"" />
  <callFunction name=""me.myFirstName"" />
  <step>Get date and time from the variables</step>
</solution><!-- END -->

<goal use=""time.currentDate,time.GetCurrentTime,time.timezone,me.UseMyFirstName"">
how long until my wife's birthday?
</goal>
<variables />
<solution>
  <callFunction name=""time.currentDate"" />
  <callFunction name=""time.GetCurrentTime"" />
  <callFunction name=""time.timezone"" />
  <callFunction name=""me.UseMyFirstName"" />
  <step>Search for wife's birthday in memory</step>
  <step>If the previous step is empty ask the user: when is your wife's birthday?</step>
</solution><!-- END -->

<goal>
Search for wife's birthday in memory
</goal>
<variables />
<solution>
  <step>Find name of wife in variables</step>
  <step>If the wife name is unknown ask the user</step>
  <step>Search for wife's birthday in Facebook using the name in memory</step>
  <step>Search for wife's birthday in Teams conversations filtering messages by name and using the name in memory</step>
  <step>Search for wife's birthday in Emails filtering messages by name and using the name in memory</step>
  <step>If the birthday cannot be found tell the user, ask the user to teach you how to find the value</step>
</solution><!-- END -->

<goal>
Search for gift ideas
</goal>
<variables />
<solution>
  <step>Find topics of interest from personal conversations</step>
  <step>Find topics of interest from personal emails</step>
  <step>Search Amazon for gifts including topics in the variables</step>
</solution><!-- END -->

<goal>
Count from 1 to 5
</goal>
<variables />
<solution>
  <step>Create a counter variable in memory with value 1</step>
  <step>Show the value of the counter variable</step>
  <step>If the counter variable is 5 stop</step>
  <step>Increment the counter variable</step>
</solution><!-- END -->

<goal>
foo bar
</goal>
<variables />
<solution>
  <noSolution>Sorry I don't know how to help with that</noSolution>
</solution><!-- END -->

The following is an incorrect example, because the solution uses a skill not listed in the 'use' attribute.

<goal use="""">
do something
</goal>
<variables />
<solution>
  <callFunction name=""time.timezone"" />
</solution><!-- END -->

End of examples.

<manual>
{{$SKILLS_MANUAL}}
</manual>

<goal use=""{{$SKILLS}}"">
{{$INPUT}}
</goal>
";

    internal const string SolveNextStepFunctionDefinition =
        @"{{$INPUT}}

Update the plan above:
* If there are steps in the solution, then:
    ** use the variables to execute the first step
    ** if the variables contains a result, replace it with the result of the first step, otherwise store the result in the variables
    ** Remove the first step.
* Keep the XML syntax correct, with a new line after the goal.
* Emit only XML.
* If the list of steps is empty, answer the goal using information in the variables, putting the solution inside the solution tag.
* Append <!-- END --> at the end.
END OF INSTRUCTIONS.

Possible updated plan:
";

    internal const string SummarizeConversationDefinition =
        @"BEGIN CONTENT TO SUMMARIZE:
{{$INPUT}}

END CONTENT TO SUMMARIZE.

Summarize the conversation in 'CONTENT TO SUMMARIZE', identifying main points of discussion and any conclusions that were reached.
Do not incorporate other general knowledge.
Summary is in plain text, in complete sentences, with no markup or tags.

BEGIN SUMMARY:
";

    internal const string GetConversationActionItemsDefinition =
        @"You are an action item extractor. You will be given chat history and need to make note of action items mentioned in the chat.
Extract action items from the content if there are any. If there are no action, return nothing. If a single field is missing, use an empty string.
Return the action items in json.

Possible statuses for action items are: Open, Closed, In Progress.

EXAMPLE INPUT WITH ACTION ITEMS:

John Doe said: ""I will record a demo for the new feature by Friday""
I said: ""Great, thanks John. We may not use all of it but it's good to get it out there.""

EXAMPLE OUTPUT:
{
    ""actionItems"": [
        {
            ""owner"": ""John Doe"",
            ""actionItem"": ""Record a demo for the new feature"",
            ""dueDate"": ""Friday"",
            ""status"": ""Open"",
            ""notes"": """"
        }
    ]
}

EXAMPLE INPUT WITHOUT ACTION ITEMS:

John Doe said: ""Hey I'm going to the store, do you need anything?""
I said: ""No thanks, I'm good.""

EXAMPLE OUTPUT:
{
    ""action_items"": []
}

CONTENT STARTS HERE.

{{$INPUT}}

CONTENT STOPS HERE.

OUTPUT:";

    internal const string GetConversationTopicsDefinition =
        @"Analyze the following extract taken from a conversation transcript and extract key topics.
- Topics only worth remembering.
- Be brief. Short phrases.
- Can use broken English.
- Conciseness is very important.
- Topics can include names of memories you want to recall.
- NO LONG SENTENCES. SHORT PHRASES.
- Return in JSON
[Input]
My name is Macbeth. I used to be King of Scotland, but I died. My wife's name is Lady Macbeth and we were married for 15 years. We had no children. Our beloved dog Toby McDuff was a famous hunter of rats in the forest.
My tragic story was immortalized by Shakespeare in a play.
[Output]
{
  ""topics"": [
    ""Macbeth"",
    ""King of Scotland"",
    ""Lady Macbeth"",
    ""Dog"",
    ""Toby McDuff"",
    ""Shakespeare"",
    ""Play"",
    ""Tragedy""
  ]
}
+++++
[Input]
{{$INPUT}}
[Output]";
}
