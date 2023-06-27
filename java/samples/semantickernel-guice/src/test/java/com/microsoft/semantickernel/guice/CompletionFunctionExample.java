// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.guice;

import com.google.inject.Guice;
import com.google.inject.Inject;
import com.google.inject.Injector;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;

import java.util.ArrayList;

public class CompletionFunctionExample {

    private final CompletionFunctionFactory completionFunctionFactory;

    public static void main(String[] args) {
        Injector injector =
                Guice.createInjector(
                        new SemanticKernelModule().withTextCompletionService("text-davinci-003"));

        CompletionFunctionExample example = injector.getInstance(CompletionFunctionExample.class);
        example.run();
    }

    @Inject
    public CompletionFunctionExample(CompletionFunctionFactory completionFunctionFactory) {
        this.completionFunctionFactory = completionFunctionFactory;
    }

    public void run() {
        String prompt = "{{$input}}\n" + "Summarize the content above.";

        String text =
                "\n"
                    + "Demo (ancient Greek poet)\n"
                    + "From Wikipedia, the free encyclopedia\n"
                    + "Demo or Damo (Greek: Δεμώ, Δαμώ; fl. c. AD 200) was a Greek woman of the\n"
                    + "Roman period, known for a single epigram, engraved upon the Colossus of\n"
                    + "Memnon, which bears her name. She speaks of herself therein as a lyric\n"
                    + "poetess dedicated to the Muses, but nothing is known of her life.[1]\n"
                    + "Identity\n"
                    + "Demo was evidently Greek, as her name, a traditional epithet of Demeter,\n"
                    + "signifies. The name was relatively common in the Hellenistic world, in\n"
                    + "Egypt and elsewhere, and she cannot be further identified. The date of her\n"
                    + "visit to the Colossus of Memnon cannot be established with certainty, but\n"
                    + "internal evidence on the left leg suggests her poem was inscribed there at\n"
                    + "some point in or after AD 196.[2]\n"
                    + "Epigram\n"
                    + "There are a number of graffiti inscriptions on the Colossus of Memnon.\n"
                    + "Following three epigrams by Julia Balbilla, a fourth epigram, in elegiac\n"
                    + "couplets, entitled and presumably authored by \"Demo\" or \"Damo\" (the\n"
                    + "Greek inscription is difficult to read), is a dedication to the Muses.[2]\n"
                    + "The poem is traditionally published with the works of Balbilla, though the\n"
                    + "internal evidence suggests a different author.[1]\n"
                    + "In the poem, Demo explains that Memnon has shown her special respect. In\n"
                    + "return, Demo offers the gift for poetry, as a gift to the hero. At the end\n"
                    + "of this epigram, she addresses Memnon, highlighting his divine status by\n"
                    + "recalling his strength and holiness.[2]\n"
                    + "Demo, like Julia Balbilla, writes in the artificial and poetic Aeolic\n"
                    + "dialect. The language indicates she was knowledgeable in Homeric\n"
                    + "poetry—'bearing a pleasant gift', for example, alludes to the use of that\n"
                    + "phrase throughout the Iliad and Odyssey.[a][2];";

        SKContext summary =
                completionFunctionFactory
                        .createFunction(
                                prompt,
                                "summarize",
                                new PromptTemplateConfig.CompletionConfig(
                                        0.2, 0.5, 0, 0, 2000))
                        .invokeAsync(text)
                        .block();

        if (summary != null) {
            System.out.println("Result: " + summary.getResult());
        } else {
            System.out.println("Null result");
        }
    }
}
