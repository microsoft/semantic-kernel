FUNCTION_FLOW_FUNCTION_DEFINITION = """
FunctionFlowFunctionDefinition =
        @"Create an XML plan step by step, to satisfy the goal given.
To create a plan, follow these steps:
1. From a <goal> create a <plan> as a series of <functions>.
2. Use only the [AVAILABLE FUNCTIONS] - do not create new functions, inputs or attribute values.
3. Only use functions that are required for the given goal.
4. A function has an 'input' and an 'output'.
5. The 'output' from each function is automatically passed as 'input' to the subsequent <function>.
6. 'input' does not need to be specified if it consumes the 'output' of the previous function.
7. To save an 'output' from a <function>, to pass into a future <function>, use <function.{FunctionName} ... setContextVariable: ""$<UNIQUE_VARIABLE_KEY>""/>
8. To save an 'output' from a <function>, to return as part of a plan result, use <function.{FunctionName} ... appendToResult: ""RESULT__$<UNIQUE_RESULT_KEY>""/>
9. Append an ""END"" XML comment at the end of the plan.
Here are some good examples:
[AVAILABLE FUNCTIONS]
  WriterSkill.Summarize:
    description: summarize input text
    inputs:
    - input: the text to summarize
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
[END AVAILABLE FUNCTIONS]
<goal>Summarize the input, then translate to japanese and email it to Martin</goal>
<plan>
  <function.WriterSkill.Summarize/>
  <function.LanguageHelpers.TranslateTo translate_to_language=""Japanese"" setContextVariable=""TRANSLATED_TEXT"" />
  <function.EmailConnector.LookupContactEmail input=""Martin"" setContextVariable=""CONTACT_RESULT"" />
  <function.EmailConnector.EmailTo input=""$TRANSLATED_TEXT"" recipient=""$CONTACT_RESULT""/>
</plan><!-- END -->
[AVAILABLE FUNCTIONS]
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
[END AVAILABLE FUNCTIONS]
<goal>Summarize an input, translate to french, and e-mail to John Doe</goal>
<plan>
    <function.AuthorAbility.Summarize/>
    <function.Magician.TranslateTo translate_to_language=""French"" setContextVariable=""TRANSLATED_SUMMARY""/>
    <function._GLOBAL_FUNCTIONS_.GetEmailAddress input=""John Doe"" setContextVariable=""EMAIL_ADDRESS""/>
    <function._GLOBAL_FUNCTIONS_.SendEmail input=""$TRANSLATED_SUMMARY"" email_address=""$EMAIL_ADDRESS""/>
</plan><!-- END -->
[AVAILABLE FUNCTIONS]
  Everything.Summarize:
    description: summarize input text
    inputs:
    - input: the text to summarize
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
[END AVAILABLE FUNCTIONS]
<goal>Create an outline for a children's book with 3 chapters about a group of kids in a club and then summarize it.</goal>
<plan>
  <function._GLOBAL_FUNCTIONS_.NovelOutline input=""A group of kids in a club called 'The Thinking Caps' that solve mysteries and puzzles using their creativity and logic."" chapterCount=""3"" />
  <function.Everything.Summarize/>
</plan><!-- END -->
End of examples.
[AVAILABLE FUNCTIONS]
{{$available_functions}}
[END AVAILABLE FUNCTIONS]
<goal>{{$input}}</goal>
";
"""
