// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Magentic;

internal sealed class MagenticPrompts
{
    private static readonly KernelPromptTemplateFactory TemplateFactory = new() { AllowDangerouslySetContent = true };

    public static readonly IPromptTemplate NewFactsTemplate = InitializePrompt(Templates.AnalyzeFacts);
    public static readonly IPromptTemplate RefreshFactsTemplate = InitializePrompt(Templates.AnalyzeFacts);
    public static readonly IPromptTemplate NewPlanTemplate = InitializePrompt(Templates.AnalyzePlan);
    public static readonly IPromptTemplate RefreshPlanTemplate = InitializePrompt(Templates.AnalyzePlan);
    public static readonly IPromptTemplate LedgerTemplate = InitializePrompt(Templates.GenerateLedger);
    public static readonly IPromptTemplate StatusTemplate = InitializePrompt(Templates.AnalyzeStatus);
    public static readonly IPromptTemplate AnswerTemplate = InitializePrompt(Templates.FinalAnswer);

    private static IPromptTemplate InitializePrompt(string template)
    {
        PromptTemplateConfig templateConfig = new() { Template = template };
        return TemplateFactory.Create(templateConfig);
    }

    public static class Parameters
    {
        public const string Task = "task";
        public const string Team = "team";
        public const string Names = "names";
        public const string Facts = "facts";
        public const string Plan = "plan";
        public const string Ledger = "ledger";
    }

    private static class Templates
    {
        public const string AnalyzeFacts =
            $$$"""
                Respond to the pre-survey in response the following user request:
                
                {{${{{Parameters.Task}}}}}

                Here is the pre-survey:

                    1. Please list any specific facts or figures that are GIVEN in the request itself. It is possible that
                       there are none.
                    2. Please list any facts that may need to be looked up, and WHERE SPECIFICALLY they might be found.
                       In some cases, authoritative sources are mentioned in the request itself.
                    3. Please list any facts that may need to be derived (e.g., via logical deduction, simulation, or computation)
                    4. Please list any facts that are recalled from memory, hunches, well-reasoned guesses, etc.

                When answering this survey, keep in mind that "facts" will typically be specific names, dates, statistics, etc.

                Your answer MUST use these headings:

                    1. GIVEN OR VERIFIED FACTS
                    2. FACTS TO LOOK UP
                    3. FACTS TO DERIVE
                    4. EDUCATED GUESSES

                DO NOT include any other headings or sections in your response. DO NOT list next steps or plans.
                """;

        public const string UpdateFacts =
            $$$"""
                As a reminder, we are working to solve the following request:

                {{${{{Parameters.Task}}}}}
                
                It's clear we aren't making as much progress as we would like, but we may have learned something new.
                Please rewrite the following fact sheet, updating it to include anything new we have learned that may be helpful.

                Example edits can include (but are not limited to) adding new guesses, moving educated guesses to verified facts
                if appropriate, etc. Updates may be made to any section of the fact sheet, and more than one section of the fact
                sheet can be edited. This is an especially good time to update educated guesses, so please at least add or update
                one educated guess or hunch, and explain your reasoning.

                Here is the old fact sheet:

                {{${{{Parameters.Facts}}}}}                
                """;

        public const string AnalyzePlan =
            $$$"""
                To address this request we have assembled the following team:

                {{${{{Parameters.Team}}}}}

                Define the most effective plan that addresses the user request.

                Ensure that the plan:

                - Is formatted as plan as a markdown list of sequential steps with each top-level bullet-point as: "{Agent Name}: {Actions, goals, or sub-list}".
                - Resolves any ambiguity or clarification of the user request
                - Only includes the team members that are required to respond to the request.
                - Excludes extra steps that are not necessary and slow down the process.
                - Does not seek final confirmation from the user.
                """;

        public const string UpdatePlan =
            $$$"""
                Please briefly explain what went wrong on this last run (the root
                cause of the failure), and then come up with a new plan that takes steps and/or includes hints to overcome prior
                challenges and especially avoids repeating the same mistakes. As before, the new plan should be concise, be expressed
                in bullet-point form, and consider the following team composition (do not involve any other outside people since we
                cannot contact anyone else):

                {{${{{Parameters.Team}}}}}                
                """;

        public const string GenerateLedger =
            $$$"""
                We are working to address the following user request:

                {{${{{Parameters.Task}}}}}


                To answer this request we have assembled the following team:

                {{${{{Parameters.Team}}}}}


                Here is an initial fact sheet to consider:

                {{${{{Parameters.Facts}}}}}


                Here is the plan to follow as best as possible:

                {{${{{Parameters.Plan}}}}}
                """;

        public const string AnalyzeStatus =
            $$$"""
                Recall we are working on the following request:

                {{${{{Parameters.Task}}}}}
                
                And we have assembled the following team:

                {{${{{Parameters.Team}}}}}
                
                To make progress on the request, please answer the following questions, including necessary reasoning:

                    - Is the request fully satisfied?  (True if complete, or False if the original request has yet to be SUCCESSFULLY and FULLY addressed)
                    - Are we in a loop where we are repeating the same requests and / or getting the same responses as before?
                      Loops can span multiple responses.
                    - Are we making forward progress? (True if just starting, or recent messages are adding value.
                      False if recent messages show evidence of being stuck in a loop or if there is evidence of the inability to proceed)
                    - Which team member is needed to respond next? (Select only from: {{${{{Parameters.Names}}}}}).
                      Always consider then initial plan but you may deviate from this plan as appropriate based on the conversation.
                    - Do not seek final confirmation from the user if the request is fully satisfied.
                    - What direction would you give this team member? (Always phrase in the 2nd person, speaking directly to them, and
                      include any specific information they may need)                    
                """;

        public const string FinalAnswer =
            $$$"""
                Synthesize a complete response to the user request using markdown format:
                {{${{{Parameters.Task}}}}}

                The complete response MUST:
                - Consider the entire conversation without incorporating information that changed or was corrected
                - NEVER include any new information not already present in the conversation
                - Capture verbatim content instead of summarizing
                - Directly address the request without narrating how the conversation progressed
                - Incorporate images specified in conversation responses
                - Include all citations or references
                - Be phrased to directly address the user
                """;
    }
}
