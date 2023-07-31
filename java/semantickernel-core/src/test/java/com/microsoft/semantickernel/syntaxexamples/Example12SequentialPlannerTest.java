// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.syntaxexamples; // Copyright (c) Microsoft. All rights

// reserved.

import static com.microsoft.semantickernel.DefaultKernelTest.mockCompletionOpenAIAsyncClient;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.coreskills.TextSkill;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.PlanningException;
import com.microsoft.semantickernel.planner.actionplanner.Plan;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import reactor.util.function.Tuples;

import java.io.IOException;

public class Example12SequentialPlannerTest {
    @Test
    public void poetrySamplesAsync() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of(
                                "Create an XML plan step by step",
                                "<plan>\n"
                                        + "<function.WriterSkill.ShortPoem input=\"John Doe\" />\n"
                                        + "<function.WriterSkill.Translate language=\"Italian\""
                                        + " setContextVariable=\"TRANSLATED_POEM\" />\n"
                                        + "<function.TextSkill.Uppercase input=\"$TRANSLATED_POEM\""
                                        + " appendToResult=\"RESULT__UPPERCASE_POEM\" />\n"
                                        + "</plan>"),
                        Tuples.of("Generate a short funny poem or limerick", "A POEM"),
                        Tuples.of(
                                "Translate the input below into Italian",
                                "a poem translated to italian"));

        SequentialPlanner planner = getSequentialPlanner(client);
        Plan plan =
                planner.createPlanAsync(
                                "Write a poem about John Doe, then translate it into Italian, then"
                                        + " convert it to uppercase.")
                        .block();
        SKContext result = plan.invokeAsync().block();
        Assertions.assertEquals("A POEM TRANSLATED TO ITALIAN", result.getResult());
    }

    @Test
    public void resultIsInvalidXml() {
        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of("Create an XML plan step by step", "<plan>"));

        SequentialPlanner planner = getSequentialPlanner(client);
        Assertions.assertThrows(
                PlanningException.class,
                () -> {
                    planner.createPlanAsync(
                                    "Write a poem about John Doe, then translate it into Italian,"
                                            + " then convert it to uppercase.")
                            .block();
                });
    }

    private static SequentialPlanner getSequentialPlanner(OpenAIAsyncClient client) {
        Kernel kernel = getKernel(client);

        return new SequentialPlanner(kernel, null, null);
    }

    private static Kernel getKernel(OpenAIAsyncClient client) {
        Kernel kernel =
                SKBuilders.kernel()
                        .withDefaultAIService(
                                SKBuilders.textCompletionService()
                                        .build(client, "text-davinci-002"))
                        .build();

        kernel.importSkillFromDirectory("SummarizeSkill", "../../samples/skills", "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", "../../samples/skills", "WriterSkill");
        kernel.importSkill(new TextSkill(), "TextSkill");
        return kernel;
    }

    public static class EmailSkill {
        @DefineSKFunction(
                name = "SendEmail",
                description = "Given an e-mail and message body, send an email")
        public void sendEmail(
                @SKFunctionInputAttribute(description = "The body of the email message to send.")
                        String input,
                @SKFunctionParameters(
                                description = "The email address to send email to.",
                                name = "email_address")
                        String emailAddress) {
            System.out.println("Emailing to " + emailAddress + "\n" + input);
        }

        @DefineSKFunction(
                name = "GetEmailAddressAsync",
                description = "Lookup an email address for a person given a name")
        public String getEmailAddressAsync(
                @SKFunctionInputAttribute(description = "The name of the person to email.")
                        String input) {
            return "fake@example.com";
        }
    }

    @Test
    public void emailSamplesAsync() throws IOException {

        OpenAIAsyncClient client =
                mockCompletionOpenAIAsyncClient(
                        Tuples.of(
                                "Create an XML plan step by step",
                                "<plan>\n"
                                        + "  <function.WriterSkill.TwoSentenceSummary/>\n"
                                        + "  <function.WriterSkill.Translate language=\"French\""
                                        + " setContextVariable=\"TRANSLATED_SUMMARY\"/>\n"
                                        + "  <function.EmailSkill.GetEmailAddressAsync input=\"John"
                                        + " Doe\" setContextVariable=\"EMAIL_ADDRESS\"/>\n"
                                        + "  <function.EmailSkill.SendEmail"
                                        + " input=\"$TRANSLATED_SUMMARY\""
                                        + " email_address=\"$EMAIL_ADDRESS\"/>\n"
                                        + "</plan>"),
                        Tuples.of(
                                "Summarize the following text in two sentences or less",
                                "Once upon a time, in a faraway kingdom, there lived a kind and"
                                    + " just king named Arjun. He ruled over his kingdom with"
                                    + " fairness and compassion, earning him the love and"
                                    + " admiration of his people. However, the kingdom was plagued"
                                    + " by a terrible dragon that lived in the nearby mountains and"
                                    + " terrorized the nearby villages, burning their crops and"
                                    + " homes. The king had tried everything to defeat the dragon,"
                                    + " but to no avail. One day, a young woman named Mira"
                                    + " approached the king and offered to help defeat the dragon."
                                    + " She was a skilled archer and claimed that she had a plan to"
                                    + " defeat the dragon once and for all. The king was skeptical,"
                                    + " but desperate for a solution, so he agreed to let her try."
                                    + " Mira set out for the dragon's lair and, with the help of"
                                    + " her trusty bow and arrow, she was able to strike the dragon"
                                    + " with a single shot through its heart, killing it instantly."
                                    + " The people rejoiced and the kingdom was at peace once"
                                    + " again. The king was so grateful to Mira that he asked her"
                                    + " to marry him and she agreed. They ruled the kingdom"
                                    + " together, ruling with fairness and compassion, just as"
                                    + " Arjun had done before. They lived happily ever after, with"
                                    + " the people of the kingdom remembering Mira as the brave"
                                    + " young woman who saved them from the dragon."),
                        Tuples.of("Translate the input below", "a poem translated to french"));

        Kernel kernel = getKernel(client);

        EmailSkill email = Mockito.spy(new EmailSkill());

        kernel.importSkill(email, "EmailSkill");

        SequentialPlanner planner = new SequentialPlanner(kernel, null, null);

        Plan plan =
                planner.createPlanAsync(
                                "Summarize an input, translate to french, and e-mail to John Doe")
                        .block();

        System.out.println("Original plan:");
        System.out.println(plan.toPlanString());

        String input =
                "Once upon a time, in a faraway kingdom, there lived a kind and just king named"
                    + " Arjun. He ruled over his kingdom with fairness and compassion, earning him"
                    + " the love and admiration of his people. However, the kingdom was plagued by"
                    + " a terrible dragon that lived in the nearby mountains and terrorized the"
                    + " nearby villages, burning their crops and homes. The king had tried"
                    + " everything to defeat the dragon, but to no avail. One day, a young woman"
                    + " named Mira approached the king and offered to help defeat the dragon. She"
                    + " was a skilled archer and claimed that she had a plan to defeat the dragon"
                    + " once and for all. The king was skeptical, but desperate for a solution, so"
                    + " he agreed to let her try. Mira set out for the dragon's lair and, with the"
                    + " help of her trusty bow and arrow, she was able to strike the dragon with a"
                    + " single shot through its heart, killing it instantly. The people rejoiced"
                    + " and the kingdom was at peace once again. The king was so grateful to Mira"
                    + " that he asked her to marry him and she agreed. They ruled the kingdom"
                    + " together, ruling with fairness and compassion, just as Arjun had done"
                    + " before. They lived happily ever after, with the people of the kingdom"
                    + " remembering Mira as the brave young woman who saved them from the dragon.";

        plan.invokeAsync(input).block();

        Mockito.verify(email, Mockito.times(1))
                .sendEmail(
                        Mockito.matches("a poem translated to french"),
                        Mockito.matches("fake@example.com"));
    }
}
