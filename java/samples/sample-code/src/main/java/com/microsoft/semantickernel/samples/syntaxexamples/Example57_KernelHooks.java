package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.ai.openai.models.ChatCompletionsOptions;
import com.azure.ai.openai.models.ChatRequestMessage;
import com.azure.ai.openai.models.ChatRequestSystemMessage;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.Kernel.Builder;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.hooks.FunctionInvokedEvent;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokedHook;
import com.microsoft.semantickernel.hooks.KernelHook.FunctionInvokingHook;
import com.microsoft.semantickernel.hooks.KernelHook.PreChatCompletionHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderedHook;
import com.microsoft.semantickernel.hooks.KernelHook.PromptRenderingHook;
import com.microsoft.semantickernel.hooks.PreChatCompletionEvent;
import com.microsoft.semantickernel.hooks.PromptRenderedEvent;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

public class Example57_KernelHooks {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) {

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        ChatCompletionService openAIChatCompletion = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        Builder kernelBuilder = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion);

        getUsageAsync(kernelBuilder.build());
        getRenderedPromptAsync(kernelBuilder.build());
        changingResultAsync(kernelBuilder.build());
        beforeInvokeCancellationAsync(kernelBuilder.build());
        afterInvokeCancellationAsync(kernelBuilder.build());
        chatCompletionHook(kernelBuilder.build());
        invocationHook(kernelBuilder.build());
    }


    /// <summary>
    /// Demonstrate using kernel invocation-hooks to monitor usage:
    /// <see cref="Kernel.FunctionInvoking"/>
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static void getUsageAsync(Kernel kernel) {
        System.out.println("\n======== Get Usage Data ========\n");

        // Initialize prompt
        String functionPrompt = "Write a random paragraph about: {{$input}}.";

        var excuseFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(functionPrompt)
            .withName("Excuse")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(100)
                .withTemperature(0.4)
                .withTopP(1)
                .build())
            .build();

        FunctionInvokingHook preHook = event -> {
            System.out.println(
                event.getFunction().getName() + " : Pre Execution Handler - Triggered");
            return event;
        };

        FunctionInvokingHook removedPreExecutionHandler = event -> {
            System.out.println(
                event.getFunction().getName() + " : Pre Execution Handler - Should not trigger");
            return event;
        };

        FunctionInvokedHook postExecutionHandler = event -> {
            System.out.println(
                event.getFunction().getName() + " : Post Execution Handler - Usage: " + event
                    .getResult()
                    .getMetadata()
                    .getUsage()
                    .getTotalTokens());
            return event;
        };

        kernel.getHookService().addHook(preHook);

        // Demonstrate pattern for removing a handler.
        kernel.getHookService().addHook("pre-invoke-removed", removedPreExecutionHandler);
        kernel.getHookService().removeHook("pre-invoke-removed");

        kernel.getHookService().addHook(postExecutionHandler);

        // Invoke prompt to trigger execution hooks.
        String input = "I missed the F1 final race";
        var result = kernel.invokeAsync(
                excuseFunction,
                KernelArguments
                    .builder()
                    .withVariable("input", input)
                    .build(),
                String.class)
            .block();
        System.out.println("Function Result: " + result.getResult());
    }


    /// <summary>
    /// Demonstrate using kernel-hooks to around prompt rendering:
    /// <see cref="Kernel.PromptRendering"/>
    /// <see cref="Kernel.PromptRendered"/>
    /// </summary>
    private static void getRenderedPromptAsync(Kernel kernel) {
        System.out.println("\n======== Get Rendered Prompt ========\n");

        // Initialize prompt
        String functionPrompt = "Write a random paragraph about: {{$input}} in the style of {{$style}}.";

        var excuseFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(functionPrompt)
            .withName("Excuse")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(100)
                .withTemperature(0.4)
                .withTopP(1)
                .build())
            .build();

        PromptRenderingHook myRenderingHandler = event -> {
            System.out.println(
                event.getFunction().getName() + " : Prompt Rendering Handler - Triggered");
            event.getArguments().put("style", ContextVariable.of("Seinfeld"));
            return event;
        };

        PromptRenderedHook myRenderedHandler = event -> {
            System.out.println(
                event.getFunction().getName() + " : Prompt Rendered Handler - Triggered");

            String prompt = event.getPrompt() + "\nUSE SHORT, CLEAR, COMPLETE SENTENCES.";

            return new PromptRenderedEvent(
                event.getFunction(),
                event.getArguments(),
                prompt
            );
        };
        kernel.getHookService().addHook(myRenderingHandler);
        kernel.getHookService().addHook(myRenderedHandler);

        // Invoke prompt to trigger execution hooks.
        String input = "I missed the F1 final race";
        var result = kernel.invokeAsync(excuseFunction,
                KernelArguments
                    .builder()
                    .withVariable("input", input)
                    .build(),
                String.class)
            .block();
        System.out.println("Function Result: " + result.getResult());
    }


    /// <summary>
    /// Demonstrate using kernel invocation-hooks to post process result:
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static void changingResultAsync(Kernel kernel) {
        System.out.println("\n======== Changing/Filtering Function Result ========\n");

        // Initialize function
        String functionPrompt = "Write a paragraph about Handlers.";

        var writerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(functionPrompt)
            .withName("Writer")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(100)
                .withTemperature(0.4)
                .withTopP(1)
                .build())
            .build();

        FunctionInvokedHook hook = event -> {
            String result = (String) event.getResult().getResult();
            result = result.replaceAll("[aeiouAEIOU0-9]", "*");

            return new FunctionInvokedEvent<>(
                event.getFunction(),
                event.getArguments(),
                new FunctionResult<>(
                    ContextVariable.of(result),
                    event.getResult().getMetadata()
                )
            );
        };
        kernel.getHookService().addHook(hook);

        // Invoke prompt to trigger execution hooks.
        var result = kernel.invokeAsync(
                writerFunction,
                KernelArguments.builder().build(),
                String.class)
            .block();
        System.out.println("Function Result: " + result.getResult());
    }


    /// <summary>
    /// Demonstrate using kernel invocation-hooks to cancel prior to execution:
    /// <see cref="Kernel.FunctionInvoking"/>
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static void beforeInvokeCancellationAsync(Kernel kernel) {
        System.out.println("\n======== Cancelling Pipeline Execution - Invoking event ========\n");

        // Initialize prompt
        String functionPrompt = "Write a paragraph about: Cancellation.";

        var writerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(functionPrompt)
            .withName("Writer")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(1000)
                .withTemperature(1)
                .withTopP(0.5)
                .build())
            .build();

        FunctionInvokingHook hook = event -> {
            System.out.println(
                event.getFunction().getName()
                    + " : FunctionInvoking - Cancelling before execution");
            throw new RuntimeException("Cancelled");
        };

        kernel.getHookService().addHook(hook);

        try {
            // Invoke prompt to trigger execution hooks.
            var result = kernel.invokeAsync(
                    writerFunction,
                    KernelArguments.builder().build(),
                    String.class)
                .block();
            System.out.println("Function Result: " + result.getResult());
        } catch (Exception e) {
            System.out.println("Exception: " + e.getMessage());
        }
    }


    /// <summary>
    /// Demonstrate using kernel invocation-hooks to cancel post after execution:
    /// <see cref="Kernel.FunctionInvoking"/>
    /// <see cref="Kernel.FunctionInvoked"/>
    /// </summary>
    private static void afterInvokeCancellationAsync(Kernel kernel) {
        System.out.println("\n======== Cancelling Pipeline Execution - Invoked event ========\n");

        // Initialize prompts
        var firstFunction = KernelFunctionFromPrompt.create("Write a phrase with Invoke.");
        var secondFunction = KernelFunctionFromPrompt.create("Write a phrase with Cancellation.");

        AtomicInteger invokingCounter = new AtomicInteger(0);
        kernel.getHookService().addHook((FunctionInvokingHook) event -> {
            invokingCounter.incrementAndGet();
            return event;
        });

        AtomicInteger invokedCounter = new AtomicInteger(0);
        kernel.getHookService().addHook((FunctionInvokedHook) event -> {
            invokedCounter.incrementAndGet();
            throw new RuntimeException("Cancelled");
        });

        // Invoke prompt to trigger execution hooks.
        try {
            var result = kernel.invokeAsync(
                    secondFunction,
                    KernelArguments.builder().build(),
                    String.class)
                .block();
            System.out.println("Function Result: " + result.getResult());
        } catch (Exception e) {
            System.out.println("Exception: " + e.getMessage());
            System.out.println("Function Invoked Times: " + invokedCounter.get());
            System.out.println("Function Invoking Times: " + invokedCounter.get());
        }
    }

    private static void chatCompletionHook(Kernel kernel) {
        // Initialize prompt
        String functionPrompt = "Write a paragraph about hats";

        var writerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(functionPrompt)
            .withName("Writer")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(1000)
                .withTemperature(1)
                .withTopP(0.5)
                .build())
            .build();

        kernel.getHookService().addPreChatCompletionHook(event -> {
            ChatCompletionsOptions options = event.getOptions();
            List<ChatRequestMessage> messages = options.getMessages();

            messages = new ArrayList<>(messages);
            messages.add(
                new ChatRequestSystemMessage("Use upper case text when responding to the prompt."));

            return new PreChatCompletionEvent(
                PreChatCompletionHook.cloneOptionsWithMessages(options, messages)
            );
        });

        try {
            // Invoke prompt to trigger execution hooks.
            var result = kernel.invokeAsync(
                    writerFunction,
                    KernelArguments.builder().build(),
                    String.class)
                .block();
            System.out.println("Function Result: " + result.getResult());
        } catch (Exception e) {
            System.out.println("Exception: " + e.getMessage());
        }
    }

    /**
     * Show use of hooks added on a single invocations.
     *
     * @param kernel
     */
    private static void invocationHook(Kernel kernel) {
        // Initialize prompt
        String functionPrompt = "Write a paragraph about hats";

        var writerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate(functionPrompt)
            .withName("Writer")
            .withDefaultExecutionSettings(PromptExecutionSettings
                .builder()
                .withMaxTokens(1000)
                .withTemperature(1)
                .withTopP(0.5)
                .build())
            .build();

        KernelHooks kernelHooks = new KernelHooks();
        kernelHooks.addPreChatCompletionHook(event -> {
            ChatCompletionsOptions options = event.getOptions();
            List<ChatRequestMessage> messages = options.getMessages();

            messages = new ArrayList<>(messages);
            messages.add(
                new ChatRequestSystemMessage("Use upper case text when responding to the prompt."));

            return new PreChatCompletionEvent(
                PreChatCompletionHook.cloneOptionsWithMessages(options, messages)
            );
        });

        try {
            // Invoke prompt to trigger execution hooks.
            var result = kernel.invokeAsync(
                    writerFunction,
                    KernelArguments.builder().build(),
                    kernelHooks,
                    String.class)
                .block();
            System.out.println("Function Result: " + result.getResult());
        } catch (Exception e) {
            System.out.println("Exception: " + e.getMessage());
        }
    }
}
