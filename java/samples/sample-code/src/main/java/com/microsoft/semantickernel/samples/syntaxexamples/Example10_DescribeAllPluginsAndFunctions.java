package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.textcompletion.OpenAITextGenerationService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.samples.plugins.text.TextPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.nio.file.Path;
import java.util.Locale;

public class Example10_DescribeAllPluginsAndFunctions {

    private static final boolean USE_AZURE_CLIENT = Boolean.parseBoolean(
        System.getenv("USE_AZURE_CLIENT"));
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // Only required if USE_AZURE_CLIENT is true
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");


    public static class StaticTextPlugin {

        @DefineKernelFunction(
            description = "Change all string chars to uppercase",
            name = "uppercase"
        )
        public static String uppercase(
            @KernelFunctionParameter(
                description = "Text to uppercase",
                name = "input"
            )
            String input) {
            return input.toUpperCase(Locale.ROOT);
        }

        @DefineKernelFunction(
            description = "Append the day variable",
            name = "appendDay"
        )
        public String appendDay(
            @KernelFunctionParameter(
                description = "Append the day variable",
                name = "appendDay"
            )
            String input,
            @KernelFunctionParameter(
                description = "Value of the day to append",
                name = "day"
            )
            String day) {
            return input + day;
        }
    }


    /// <summary>
/// Print a list of all the functions imported into the kernel, including function descriptions,
/// list of parameters, parameters descriptions, etc.
/// See the end of the file for a sample of what the output looks like.
/// </summary>
    public static void main(String[] args) {
        TextGenerationService textGenerationService;

        if (USE_AZURE_CLIENT) {
            OpenAIAsyncClient client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

            textGenerationService = OpenAITextGenerationService.builder()
                .withOpenAIAsyncClient(client)
                .withModelId("text-davinci-003")
                .build();
        } else {
            OpenAIAsyncClient client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();

            // TODO: Add support for OpenAI API
            textGenerationService = null;
        }

        Kernel kernel = Kernel.builder()
            .withDefaultAIService(TextGenerationService.class, textGenerationService)
            .build();

        kernel.getPlugins().add(
            KernelPluginFactory.createFromObject(
                new StaticTextPlugin(), "StaticTextPlugin")
        );

        // Import another native plugin
        kernel.getPlugins().add(
            KernelPluginFactory.createFromObject(
                new TextPlugin(), "AnotherTextPlugin")
        );

        kernel.getPlugins().add(
            KernelPluginFactory
                .importPluginFromDirectory(
                    Path.of("java/samples/sample-code/src/main/resources/Plugins"),
                    "SummarizePlugin",
                    null)
        );

        // Not added to kernel so should not be printed
        var jokeFunction = KernelFunctionFromPrompt.builder()
            .withTemplate("tell a joke about {{$input}}")
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withMaxTokens(150)
                    .build()
            )
            .build();

        // Not added to kernel so should not be printed
        var writeNovel = KernelFunctionFromPrompt.builder()
            .withTemplate("write a novel about {{$input}} in {{$language}} language")
            .withName("Novel")
            .withDescription("Write a bedtime story")
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withMaxTokens(150)
                    .build()
            )
            .build();

        System.out.println("**********************************************");
        System.out.println("****** Registered plugins and functions ******");
        System.out.println("**********************************************");
        System.out.println();

        kernel.getPlugins()
            .forEach(plugin -> {
                System.out.println("Plugin: " + plugin.getName());
                plugin
                    .getFunctions()
                    .values()
                    .stream()
                    .map(KernelFunction::getMetadata)
                    .forEach(Example10_DescribeAllPluginsAndFunctions::printFunction);
            });
    }

    private static void printFunction(KernelFunctionMetadata func) {
        System.out.println("   " + func.getName() + ": " + func.getDescription());

        if (func.getParameters().size() > 0) {
            System.out.println("      Params:");

            func.getParameters()
                .forEach(p -> {
                    System.out.println("      - " + p.getName() + ": " + p.getDescription());
                    System.out.println("        default: '" + p.getDefaultValue() + "'");
                });
        }

        System.out.println();
    }
}