package com.microsoft.semantickernel.syntaxexamples;

import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.WireMockConfiguration;
import com.microsoft.semantickernel.samples.syntaxexamples.Example01_NativeFunctions;
import com.microsoft.semantickernel.samples.syntaxexamples.Example03_Arguments;
import com.microsoft.semantickernel.samples.syntaxexamples.Example05_InlineFunctionDefinition;
import com.microsoft.semantickernel.samples.syntaxexamples.Example06_TemplateLanguage;
import com.microsoft.semantickernel.samples.syntaxexamples.Example09_FunctionTypes;
import com.microsoft.semantickernel.samples.syntaxexamples.Example10_DescribeAllPluginsAndFunctions;
import com.microsoft.semantickernel.samples.syntaxexamples.Example13_ConversationSummaryPlugin;
import com.microsoft.semantickernel.samples.syntaxexamples.Example17_ChatGPT;
import com.microsoft.semantickernel.samples.syntaxexamples.Example27_PromptFunctionsUsingChatGPT;
import com.microsoft.semantickernel.samples.syntaxexamples.Example33_Chat;
import com.microsoft.semantickernel.samples.syntaxexamples.Example41_HttpClientUsage;
import com.microsoft.semantickernel.samples.syntaxexamples.Example43_GetModelResult;
import com.microsoft.semantickernel.samples.syntaxexamples.Example44_MultiChatCompletion;
import com.microsoft.semantickernel.samples.syntaxexamples.Example49_LogitBias;
import com.microsoft.semantickernel.samples.syntaxexamples.Example55_TextChunker;
import com.microsoft.semantickernel.samples.syntaxexamples.Example56_TemplateMethodFunctionsWithMultipleArguments;
import com.microsoft.semantickernel.samples.syntaxexamples.Example57_KernelHooks;
import com.microsoft.semantickernel.samples.syntaxexamples.Example58_ConfigureExecutionSettings;
import com.microsoft.semantickernel.samples.syntaxexamples.Example60_AdvancedMethodFunctions;
import com.microsoft.semantickernel.samples.syntaxexamples.Example61_MultipleLLMs;
import com.microsoft.semantickernel.samples.syntaxexamples.Example62_CustomAIServiceSelector;
import com.microsoft.semantickernel.samples.syntaxexamples.Example63_ChatCompletionPrompts;
import com.microsoft.semantickernel.samples.syntaxexamples.Example64_MultiplePromptTemplates;
import com.microsoft.semantickernel.samples.syntaxexamples.Example69_MutableKernelPlugin;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

public class WiremockExamplesIT {

    public static List<Class<?>> mains = Arrays.asList(

        Example01_NativeFunctions.class,
        Example03_Arguments.class,
        Example05_InlineFunctionDefinition.class,
        Example06_TemplateLanguage.class,
        //Example08_RetryHandler.class,
        Example09_FunctionTypes.class,
        Example10_DescribeAllPluginsAndFunctions.class,
        //Example11_WebSearchQueries.class,
        Example13_ConversationSummaryPlugin.class,
        Example17_ChatGPT.class,
        //Example26_AADAuth.class,

        Example27_PromptFunctionsUsingChatGPT.class,

        // Difficulty with time causing wiremock to fail
        //Example30_ChatWithPrompts.class,
        Example33_Chat.class,
        Example41_HttpClientUsage.class,
        Example43_GetModelResult.class,
        Example44_MultiChatCompletion.class,
        Example49_LogitBias.class,
        Example55_TextChunker.class,
        Example56_TemplateMethodFunctionsWithMultipleArguments.class,
        Example57_KernelHooks.class,
        Example58_ConfigureExecutionSettings.class,
        Example60_AdvancedMethodFunctions.class,
        Example61_MultipleLLMs.class,
        Example62_CustomAIServiceSelector.class,
        Example63_ChatCompletionPrompts.class,
        Example64_MultiplePromptTemplates.class,
        Example69_MutableKernelPlugin.class
    );

    public static WireMockServer createWiremockServer(String dir) {
        return new WireMockServer(
            WireMockConfiguration.wireMockConfig()
                .httpsPort(8443)
                .trustStorePath("scripts/client.truststore")
                .trustStorePassword("password")
                .trustStoreType("jks")
                .keystorePath("scripts/server.keystore")
                .keystorePassword("password")
                .keystoreType("jks")
                .usingFilesUnderDirectory(dir)
        );
    }

    public static void main(String[] args) {
        new WiremockExamplesIT()
            .runSamplesTest()
            .forEach(it -> {
                try {
                    it.getExecutable().execute();
                } catch (Throwable e) {
                    throw new RuntimeException(e);
                }
            });
    }

    @TestFactory
    public Stream<DynamicTest> runSamplesTest() {
        return mains
            .stream()
            .map(
                testClazz -> DynamicTest
                    .dynamicTest(
                        testClazz.getSimpleName() + "Test",
                        () -> {
                            System.out.println("Running: " + testClazz.getSimpleName());
                            WireMockServer server = null;
                            try {
                                Method main = testClazz.getMethod("main",
                                    String[].class);

                                server = createWiremockServer("src/test/resources/wiremock");

                                server.start();
                                main.invoke(null, new Object[]{null});
                            } catch (Exception e) {
                                e.printStackTrace();
                                throw new RuntimeException(e);
                            } finally {
                                if (server != null) {
                                    server.stop();
                                }
                            }
                        }));
    }
}
