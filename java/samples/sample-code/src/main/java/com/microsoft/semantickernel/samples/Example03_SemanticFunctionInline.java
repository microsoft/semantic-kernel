///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS com.microsoft.semantic-kernel:semantickernel-core:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel:semantickernel-core-skills:0.2.6-alpha
//DEPS com.microsoft.semantic-kernel.connectors:semantickernel-connectors:0.2.6-alpha
//DEPS org.slf4j:slf4j-jdk14:2.0.7
//SOURCES syntaxexamples/SampleSkillsUtil.java,Config.java,Example00_GettingStarted.java
package com.microsoft.semantickernel.samples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import reactor.core.publisher.Mono;

import java.io.IOException;

/**
 * Define a Semantic Function inline with Java code.
 */
public class Example03_SemanticFunctionInline {

    /**
     * Defines and runs an inline Semantic Function
     *
     * @param kernel       Kernel with Text Completion
     * @param prompt       String prompt
     * @param functionName Name of the function
     * @param text         Input to the function
     */
    public static void inlineFunction(Kernel kernel, String prompt, String functionName, String text) {
        SKFunction summarize = kernel
                .getSemanticFunctionBuilder()
                .withPromptTemplate(prompt)
                .withFunctionName(functionName)
                .withCompletionConfig(
                        new PromptTemplateConfig.CompletionConfig(
                                0.2,
                                0.5,
                                0,
                                0,
                                2000))
                .build();

        Mono<SKContext> result = summarize.invokeAsync(text);

        if (result != null) {
            System.out.println(result.block().getResult());
        }
    }

    /**
     * Example prompt that summarizes text
     *
     * @param kernel
     */
    public static void summarize(Kernel kernel) {
        String prompt = """
                {{$input}}
                Summarize the content above.
                """;

        String text = """
                Demo (ancient Greek poet)
                From Wikipedia, the free encyclopedia
                Demo or Damo (Greek: Δεμώ, Δαμώ; fl. c. AD 200) was a Greek woman of the Roman period,
                known for a single epigram, engraved upon the Colossus of Memnon, which bears her name.
                She speaks of herself therein as a lyric poetess dedicated to the Muses, but nothing is known of her life.[1]
                Identity
                Demo was evidently Greek, as her name, a traditional epithet of Demeter, signifies.
                The name was relatively common in the Hellenistic world, in Egypt and elsewhere,
                and she cannot be further identified.
                The date of her visit to the Colossus of Memnon cannot be established with certainty,
                but internal evidence on the left leg suggests her poem was inscribed there at some point in or after AD 196.[2]
                Epigram
                There are a number of graffiti inscriptions on the Colossus of Memnon.
                Following three epigrams by Julia Balbilla, a fourth epigram, in elegiac couplets,
                entitled and presumably authored by "Demo" or "Damo"
                (the Greek inscription is difficult to read), is a dedication to the Muses.[2]
                The poem is traditionally published with the works of Balbilla,
                though the internal evidence suggests a different author.[1]
                In the poem, Demo explains that Memnon has shown her special respect.
                In return, Demo offers the gift for poetry, as a gift to the hero.
                At the end of this epigram, she addresses Memnon,
                highlighting his divine status by recalling his strength and holiness.[2]
                Demo, like Julia Balbilla, writes in the artificial and poetic Aeolic dialect.
                The language indicates she was knowledgeable in Homeric poetry—'bearing a pleasant gift',
                for example, alludes to the use of that phrase throughout the Iliad and Odyssey.[a][2]
                """;

        inlineFunction(kernel, prompt, "summarize", text);
    }

    /**
     * Example of a prompt returning a TLDR of a text
     *
     * @param kernel
     */
    public static void TLDR(Kernel kernel) {
        String propmt = """
                {{$input}}

                Give me the TLDR in 5 words.
                """;

        String text = """
                    1) A robot may not injure a human being or, through inaction,
                    allow a human being to come to harm.

                    2) A robot must obey orders given it by human beings except where
                    such orders would conflict with the First Law.

                    3) A robot must protect its own existence as long as such protection
                    does not conflict with the First or Second Law.
                """;

        inlineFunction(kernel, propmt, "tldr", text);
    }

    public static void run(OpenAIAsyncClient client) throws IOException {
        Kernel kernel = Example00_GettingStarted.getKernel(client);

        summarize(kernel);
        TLDR(kernel);
    }

    public static void main(String args[]) throws ConfigurationException, IOException {
        run(OpenAIClientProvider.getClient());
    }
}
