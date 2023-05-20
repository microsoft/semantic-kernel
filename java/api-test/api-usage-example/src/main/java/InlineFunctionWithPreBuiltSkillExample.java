// Copyright (c) Microsoft. All rights reserved.
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.openai.AzureOpenAIClient;
import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Properties;

public class InlineFunctionWithPreBuiltSkillExample {
    public static final String AZURE_CONF_PROPERTIES = "conf.properties";

    private static final Logger LOGGER =
            LoggerFactory.getLogger(InlineFunctionWithPreBuiltSkillExample.class);

    private static final String MODEL = "text-davinci-003";

    private static final String TEXT_TO_SUMMARIZE =
            "Demo (ancient Greek poet)\n"
                    + "From Wikipedia, the free encyclopedia\n"
                    + "Demo or Damo (Greek: Δεμώ, Δαμώ; fl. c. AD 200) was a Greek woman of the"
                    + " Roman period, known for a single epigram, engraved upon the Colossus of"
                    + " Memnon, which bears her name. She speaks of herself therein as a lyric"
                    + " poetess dedicated to the Muses, but nothing is known of her life.[1]\n"
                    + "Identity\n"
                    + "Demo was evidently Greek, as her name, a traditional epithet of Demeter,"
                    + " signifies. The name was relatively common in the Hellenistic world, in"
                    + " Egypt and elsewhere, and she cannot be further identified. The date of her"
                    + " visit to the Colossus of Memnon cannot be established with certainty, but"
                    + " internal evidence on the left leg suggests her poem was inscribed there at"
                    + " some point in or after AD 196.[2]\n"
                    + "Epigram\n"
                    + "There are a number of graffiti inscriptions on the Colossus of Memnon."
                    + " Following three epigrams by Julia Balbilla, a fourth epigram, in elegiac"
                    + " couplets, entitled and presumably authored by \"Demo\" or \"Damo\" (the"
                    + " Greek inscription is difficult to read), is a dedication to the Muses.[2]"
                    + " The poem is traditionally published with the works of Balbilla, though the"
                    + " internal evidence suggests a different author.[1]\n"
                    + "In the poem, Demo explains that Memnon has shown her special respect. In"
                    + " return, Demo offers the gift for poetry, as a gift to the hero. At the end"
                    + " of this epigram, she addresses Memnon, highlighting his divine status by"
                    + " recalling his strength and holiness.[2]\n"
                    + "Demo, like Julia Balbilla, writes in the artificial and poetic Aeolic"
                    + " dialect. The language indicates she was knowledgeable in Homeric"
                    + " poetry—'bearing a pleasant gift', for example, alludes to the use of that"
                    + " phrase throughout the Iliad and Odyssey.[a][2]\n";

    public static String getToken(String configName) throws IOException {
        return getConfigValue(configName, "token");
    }

    public static String getEndpoint(String configName) throws IOException {
        return getConfigValue(configName, "endpoint");
    }

    private static String getConfigValue(String configName, String propertyName)
            throws IOException {
        String home = new File(System.getProperty("user.home")).getAbsolutePath();

        try (FileInputStream fis = new FileInputStream(home + "/.oai/" + configName)) {
            Properties props = new Properties();
            props.load(fis);
            String apiKey = props.getProperty(propertyName);
            if (apiKey == null) {
                System.err.println("NO PROPERTY " + propertyName);
                return "";
            }
            return apiKey;
        }
    }

    public static void main(String[] args) throws IOException {
        String apiKey = getToken(AZURE_CONF_PROPERTIES);

        OpenAIAsyncClient client =
                new AzureOpenAIClient(
                        new OpenAIClientBuilder()
                                .endpoint(getEndpoint(AZURE_CONF_PROPERTIES))
                                .credential(new AzureKeyCredential(apiKey))
                                .buildAsyncClient());

        TextCompletion textCompletion = SKBuilders.textCompletionService().build(client, MODEL);

        String prompt = "{{$input}}\nSummarize the content above.";

        CompletionSKFunction summarizeFunc =
                SKBuilders.completionFunctions()
                        .createFunction(
                                prompt,
                                "summarize",
                                null,
                                null,
                                new PromptTemplateConfig.CompletionConfig(
                                        0.2, 0.5, 0, 0, 2000, new ArrayList<>()));

        KernelConfig kernelConfig =
                new KernelConfig.Builder()
                        .addTextCompletionService(MODEL, kernel -> textCompletion)
                        .addSkill(summarizeFunc)
                        .build();

        Kernel kernel = SKBuilders.kernel().setKernelConfig(kernelConfig).build();

        CompletionSKFunction summarize =
                kernel.getSkills().getFunction("summarize", CompletionSKFunction.class);

        if (summarize == null) {
            throw new RemoteException("No function");
        }

        CompletionSKContext context = summarize.invokeAsync(TEXT_TO_SUMMARIZE).block();

        if (context != null) {
            LOGGER.info("Result: " + context.getResult());
        } else {
            LOGGER.error("Null result");
        }
    }
}
