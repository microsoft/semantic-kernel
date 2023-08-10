// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.http.policy.ExponentialBackoffOptions;
import com.azure.core.http.policy.RetryOptions;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.util.AzureOpenAISettings;
import com.microsoft.semantickernel.connectors.ai.openai.util.SettingsMap;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.time.Duration;

import static com.microsoft.semantickernel.SamplesConfig.DEFAULT_PROPERTIES_LOCATIONS;

public class Example08_RetryHandler {

    public static void main(String[] args) throws ConfigurationException {
        RetryOptions retryOptions = new RetryOptions(new ExponentialBackoffOptions()
                .setMaxDelay(Duration.ofSeconds(180))
                .setBaseDelay(Duration.ofSeconds(60))
                .setMaxRetries(3));

        AzureOpenAISettings settings = new AzureOpenAISettings(SettingsMap.getWithAdditional(DEFAULT_PROPERTIES_LOCATIONS));

        OpenAIAsyncClient client = new OpenAIClientBuilder()
                .retryOptions(retryOptions)
                .endpoint(settings.getEndpoint())
                .credential(new AzureKeyCredential(settings.getKey()))
                .buildAsyncClient();

        String text = """
                Demo (ancient Greek poet)
                    From Wikipedia, the free encyclopedia
                    Demo or Damo (Greek: Δεμώ, Δαμώ; fl. c. AD 200) was a Greek woman of the
                     Roman period, known for a single epigram, engraved upon the Colossus of
                     Memnon, which bears her name. She speaks of herself therein as a lyric
                     poetess dedicated to the Muses, but nothing is known of her life.[1]
                    Identity
                    Demo was evidently Greek, as her name, a traditional epithet of Demeter,
                     signifies. The name was relatively common in the Hellenistic world, in
                     Egypt and elsewhere, and she cannot be further identified. The date of her
                     visit to the Colossus of Memnon cannot be established with certainty, but
                     internal evidence on the left leg suggests her poem was inscribed there at
                     some point in or after AD 196.[2]
                    Epigram
                    There are a number of graffiti inscriptions on the Colossus of Memnon.
                     Following three epigrams by Julia Balbilla, a fourth epigram, in elegiac
                     couplets, entitled and presumably authored by "Demo" or "Damo" (the
                     Greek inscription is difficult to read), is a dedication to the Muses.[2]
                     The poem is traditionally published with the works of Balbilla, though the
                     internal evidence suggests a different author.[1]
                    In the poem, Demo explains that Memnon has shown her special respect. In
                     return, Demo offers the gift for poetry, as a gift to the hero. At the end
                     of this epigram, she addresses Memnon, highlighting his divine status by
                     recalling his strength and holiness.[2]
                    Demo, like Julia Balbilla, writes in the artificial and poetic Aeolic
                     dialect. The language indicates she was knowledgeable in Homeric
                     poetry—'bearing a pleasant gift', for example, alludes to the use of that
                     phrase throughout the Iliad and Odyssey.[a][2];
                """;

        String prompt = "{{$input}}\nSummarize the content above.";

        TextCompletion textCompletion = SKBuilders.textCompletionService()
                .setModelId("text-davinci-003")
                .withOpenAIClient(client)
                .build();

        Kernel kernel = SKBuilders
                .kernel()
                .withDefaultAIService(textCompletion)
                .build();

        CompletionSKFunction summarizeFunc = SKBuilders
                .completionFunctions()
                .withKernel(kernel)
                .setPromptTemplate(prompt)
                .setFunctionName("summarize")
                .setCompletionConfig(
                        new PromptTemplateConfig.CompletionConfig(
                                0.2, 0.5, 0, 0, 2000))
                .build();

        kernel.registerSemanticFunction(summarizeFunc);

        SKContext context = summarizeFunc.invokeAsync(text).block();

        System.out.println(context.getResult());
    }
}
