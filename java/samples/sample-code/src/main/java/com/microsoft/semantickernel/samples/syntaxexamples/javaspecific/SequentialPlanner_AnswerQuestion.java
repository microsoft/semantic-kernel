package com.microsoft.semantickernel.samples.syntaxexamples.javaspecific;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class SequentialPlanner_AnswerQuestion {

    public static class InformationFinder {
        @DefineSKFunction(
                name = "Search",
                description = "Returns information relevant to answering a given query."
        )
        public String search(
                @SKFunctionInputAttribute(description = "The query to answer.")
                String query) {
            return """
                    - The Eiffel Tower is in Paris.
                    - The Eiffel Tower is made of metal.
                    - The Eiffel Tower is 324 meters tall.
                    """.stripIndent();
        }
    }

    public static void main(String[] args) throws IOException, ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();
        var kernel = SKBuilders.kernel()
                .withDefaultAIService(SKBuilders.textCompletionService()
                        .build(client, "text-davinci-003"))
                .build();


        kernel.importSkillFromResources(
                "Plugins",
                "Answer",
                "AnswerQuestion",
                SequentialPlanner_AnswerQuestion.class
        );

        kernel.importSkill(new InformationFinder(), "InformationFinder");

        String prompt;
        try (InputStream altprompt = SequentialPlanner_AnswerQuestion.class.getResourceAsStream("require_context_variable_planner_prompt.txt")) {
            prompt = new String(altprompt.readAllBytes(), StandardCharsets.UTF_8);
        }

        var planner = new SequentialPlanner(kernel, null, prompt);

        var plan = planner.createPlanAsync("Take the input as a question and answer it finding any information needed.").block();

        System.out.println(plan.toPlanString());

        SKContext response = plan.invokeAsync("Where is the Eiffel Tower?").block();

        System.out.println("========================================");
        System.out.println("Answer is: " + response.getResult());
        System.out.println("Sources used to answer this question: " + response.getVariables().get("sources"));
    }
}
