// Copyright (c) Microsoft. All rights reserved.
import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class InlineFunctionExample {
    public static final String AZURE_CONF_PROPERTIES = "conf.properties";
    private static final Logger LOGGER = LoggerFactory.getLogger(InlineFunctionExample.class);
    private static final String MODEL = "text-davinci-003";

    private static final String API_KEY;
    private static final String ENDPOINT;
    private static final String TEXT_TO_SUMMARIZE =
            """
                    Demo (ancient Greek poet)
                       From Wikipedia, the free encyclopedia
                       Demo or Damo (Greek: Δεμώ, Δαμώ; fl. c. AD 200) was a Greek woman of the
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

    static {
        try {
            API_KEY = getToken();
            ENDPOINT = getEndpoint();
        } catch (IOException e) {
            throw new ExceptionInInitializerError(
                    "Error reading config file or properties. " + e.getMessage());
        }
    }

    private static String getToken() throws IOException {
        return getConfigValue("token");
    }

    private static String getEndpoint() throws IOException {
        return getConfigValue("endpoint");
    }

    private static String getConfigValue(String propertyName) throws IOException {
        String propertyValue;
        Path configPath = Paths.get(System.getProperty("user.home"), ".oai", AZURE_CONF_PROPERTIES);
        Properties props = new Properties();
        try (var reader = Files.newBufferedReader(configPath)) {
            props.load(reader);
            propertyValue = props.getProperty(propertyName);
            if (propertyValue == null || propertyValue.isEmpty()) {
                throw new IOException("No property for: " + propertyName + " in " + configPath);
            }
        } catch (IOException e) {
            throw new IOException("Please create a file at " + configPath, e);
        }
        return propertyValue;
    }

    public static void main(String[] args) {
        OpenAIAsyncClient client =
                new OpenAIClientBuilder()
                        .endpoint(ENDPOINT)
                        .credential(new AzureKeyCredential(API_KEY))
                        .buildAsyncClient();

        TextCompletion textCompletion =
                SKBuilders.textCompletion().withOpenAIClient(client).withModelId(MODEL).build();
        String prompt = "{{$input}}\n" + "Summarize the content above.";

        Kernel kernel = SKBuilders.kernel().withDefaultAIService(textCompletion).build();

        CompletionSKFunction summarize =
                kernel.getSemanticFunctionBuilder()
                        .withPromptTemplate(prompt)
                        .withFunctionName("summarize")
                        .withCompletionConfig(
                                new PromptTemplateConfig.CompletionConfig(0.2, 0.5, 0, 0, 2000))
                        .build();

        if (summarize == null) {
            LOGGER.error("Null function");
            return;
        }

        CountDownLatch cdl = new CountDownLatch(1);
        summarize
                .invokeAsync(TEXT_TO_SUMMARIZE)
                .subscribe(
                        context -> LOGGER.info("Result: {} ", context.getResult()),
                        error -> {
                            LOGGER.error("Error: {} ", error.getMessage());
                            cdl.countDown();
                        },
                        () -> {
                            LOGGER.info("Completed");
                            cdl.countDown();
                        });
        try {
            cdl.await();
        } catch (InterruptedException e) {
            LOGGER.error("Error: {} ", e.getMessage());
        }
    }
}
