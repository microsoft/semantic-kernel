// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.coreskills.TextSkill;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlanner;
import com.microsoft.semantickernel.planner.sequentialplanner.SequentialPlannerRequestSettings;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionInputAttribute;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Set;

public class Example12_SequentialPlanner {

    private static final Logger LOGGER = LoggerFactory.getLogger(Example12_SequentialPlanner.class);

    public static void main(String[] args) throws ConfigurationException {
        poetrySamplesAsync();
        emailSamplesAsync();
        bookSamplesAsync();
        //MemorySampleAsync();
    }

    private static void poetrySamplesAsync() throws ConfigurationException {
        System.out.println("======== Sequential Planner - Create and Execute Poetry Plan ========");
        var kernel = initializeKernel();

        kernel.importSkill(new TextSkill(), "TextSkill");

        var planner = new SequentialPlanner(kernel, null, null);

        var plan = planner.createPlanAsync("Write a poem about John Doe, then translate it into Italian, then convert it to uppercase.").block();

        // Original plan:
        // Goal: Write a poem about John Doe, then translate it into Italian.

        // Steps:
        // - WriterSkill.ShortPoem INPUT='John Doe is a friendly guy who likes to help others and enjoys reading books.' =>
        // - WriterSkill.Translate language='Italian' INPUT='' =>

        SKContext result = plan.invokeAsync().block();

        System.out.println("Result:");
        System.out.println(result.getResult());
    }

    public static class EmailSkill {
        @DefineSKFunction(name = "SendEmail", description = "Given an e-mail and message body, send an email")
        public void sendEmail(
                @SKFunctionInputAttribute(description = "The body of the email message to send.")
                String input,
                @SKFunctionParameters(description = "The email address to send email to.", name = "email_address")
                String emailAddress
        ) {
            LOGGER.info("Emailing to " + emailAddress + "\n" + input);
        }

        @DefineSKFunction(name = "GetEmailAddressAsync", description = "Lookup an email address for a person given a name")
        public String getEmailAddressAsync(
                @SKFunctionInputAttribute(description = "The name of the person to email.")
                String input) {
            return "fake@example.com";
        }
    }

    private static void emailSamplesAsync() throws ConfigurationException {
        System.out.println("======== Sequential Planner - Create and Execute Email Plan ========");
        var kernel = initializeKernel();

        kernel.importSkill(new EmailSkill(), "email");


        SequentialPlanner planner = initPlanner(kernel, 1024);

        var plan = planner.createPlanAsync("Summarize an input, translate to french, and e-mail to John Doe").block();

        // Original plan:
        // Goal: Summarize an input, translate to french, and e-mail to John Doe

        // Steps:
        // - SummarizeSkill.Summarize INPUT='' =>
        // - WriterSkill.Translate language='French' INPUT='' => TRANSLATED_SUMMARY
        // - email.GetEmailAddress INPUT='John Doe' => EMAIL_ADDRESS
        // - email.SendEmail INPUT='$TRANSLATED_SUMMARY' email_address='$EMAIL_ADDRESS' =>

        System.out.println("Original plan:");
        System.out.println(plan.toManualString(false));

        var input =
                "Once upon a time, in a faraway kingdom, there lived a kind and just king named Arjun. " +
                        "He ruled over his kingdom with fairness and compassion, earning him the love and admiration of his people. " +
                        "However, the kingdom was plagued by a terrible dragon that lived in the nearby mountains and terrorized the nearby villages, " +
                        "burning their crops and homes. The king had tried everything to defeat the dragon, but to no avail. " +
                        "One day, a young woman named Mira approached the king and offered to help defeat the dragon. She was a skilled archer " +
                        "and claimed that she had a plan to defeat the dragon once and for all. The king was skeptical, but desperate for a solution, " +
                        "so he agreed to let her try. Mira set out for the dragon's lair and, with the help of her trusty bow and arrow, " +
                        "she was able to strike the dragon with a single shot through its heart, killing it instantly. The people rejoiced " +
                        "and the kingdom was at peace once again. The king was so grateful to Mira that he asked her to marry him and she agreed. " +
                        "They ruled the kingdom together, ruling with fairness and compassion, just as Arjun had done before. They lived " +
                        "happily ever after, with the people of the kingdom remembering Mira as the brave young woman who saved them from the dragon.";

        plan.invokeAsync(input).blockOptional();
    }

    private static void bookSamplesAsync() throws ConfigurationException {
        System.out.println("======== Sequential Planner - Create and Execute Book Creation Plan  ========");
        var kernel = initializeKernel();

        SequentialPlanner planner = initPlanner(kernel, 1024);

        var plan = planner.createPlanAsync("Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'").block();

        // Original plan:
        // Goal: Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'

        // Steps:
        // - WriterSkill.NovelOutline chapterCount='3' INPUT='A group of kids in a club called 'The Thinking Caps' that solve mysteries and puzzles using their creativity and logic.' endMarker='<!--===ENDPART===-->' => OUTLINE
        // - MiscSkill.ElementAtIndex count='3' INPUT='$OUTLINE' index='0' => CHAPTER_1_SYNOPSIS
        // - WriterSkill.NovelChapter chapterIndex='1' previousChapter='' INPUT='$CHAPTER_1_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_1
        // - MiscSkill.ElementAtIndex count='3' INPUT='$OUTLINE' index='1' => CHAPTER_2_SYNOPSIS
        // - WriterSkill.NovelChapter chapterIndex='2' previousChapter='$CHAPTER_1_SYNOPSIS' INPUT='$CHAPTER_2_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_2
        // - MiscSkill.ElementAtIndex count='3' INPUT='$OUTLINE' index='2' => CHAPTER_3_SYNOPSIS
        // - WriterSkill.NovelChapter chapterIndex='3' previousChapter='$CHAPTER_2_SYNOPSIS' INPUT='$CHAPTER_3_SYNOPSIS' theme='Children's mystery' => RESULT__CHAPTER_3
        System.out.println(plan.invokeAsync().block().getResult());
    }

    /*
    TODO
    private static void memorySampleAsync() throws IOException {
        System.out.println("======== Sequential Planner - Create and Execute Plan using Memory ========");
        var kernel = initializeKernel();

        SequentialPlanner planner = initPlanner(kernel, 1024);

        kernel.importSkillsFromDirectory("samples/skills",
                "CalendarSkill",
                "ChatSkill",
                "ChildrensBookSkill",
                "ClassificationSkill",
                "CodingSkill",
                "FunSkill",
                "IntentDetectionSkill",
                "MiscSkill",
                "QASkill");

        kernel.importSkill(new EmailSkill(), "email");
        kernel.importSkill(new StaticTextSkill(), "statictext");
        kernel.importSkill(new TextSkill(), "text");
        kernel.importSkill(new Microsoft.SemanticKernel.CoreSkills.TextSkill(), "coretext");

        var goal = "Create a book with 3 chapters about a group of kids in a club called 'The Thinking Caps.'";

        var planner = new SequentialPlanner(kernel, new SequentialPlannerConfig {
            RelevancyThreshold =0.78
        });

        var plan = await planner.CreatePlanAsync(goal);

        System.out.println("Original plan:");
        System.out.println(plan.ToPlanString());
    }

     */

    private static Kernel initializeKernel() throws ConfigurationException {
        OpenAIAsyncClient client = SamplesConfig.getClient();
        var kernel = SKBuilders.kernel()
                .withDefaultAIService(SKBuilders.chatCompletion()
                        .withOpenAIClient(client)
                        .setModelId("gpt-35-turbo")
                        .build())
                .withMemory(SKBuilders
                        .semanticTextMemory()
                        .setEmbeddingGenerator(
                                SKBuilders.textEmbeddingGenerationService()
                                        .withOpenAIClient(client)
                                        .setModelId("gpt-35-turbo")
                                        .build()
                        )
                        .setStorage(new VolatileMemoryStore())
                        .build())
                .build();


        // Load additional skills to enable planner to do non-trivial asks.
        kernel.importSkillFromDirectory("SummarizeSkill", SampleSkillsUtil.detectSkillDirLocation(), "SummarizeSkill");
        kernel.importSkillFromDirectory("WriterSkill", SampleSkillsUtil.detectSkillDirLocation(), "WriterSkill");
        kernel.importSkillFromDirectory("MiscSkill", SampleSkillsUtil.detectSkillDirLocation(), "MiscSkill");

        return kernel;
    }

    private static SequentialPlanner initPlanner(Kernel kernel, int maxTokens) {
        return new SequentialPlanner(kernel, new SequentialPlannerRequestSettings(
                null,
                100,
                Set.of(),
                Set.of(),
                Set.of(),
                maxTokens
        ), null);
    }
}
