package com.microsoft.semantickernel.samples.syntaxexamples;

import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.DefaultKernel;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.textcompletion.OpenAITextGenerationService;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.Temporal;
import java.util.Date;
import java.util.List;
import reactor.core.publisher.Mono;

public class Example09_FunctionTypes {

    private static final boolean USE_AZURE_CLIENT = Boolean.parseBoolean(
        System.getenv("USE_AZURE_CLIENT"));
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // Only required if USE_AZURE_CLIENT is true
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");


    private static class DateTimeContextVariableTypeConverter extends
        ContextVariableTypeConverter<ZonedDateTime> {

        private static final List<Converter<ZonedDateTime, ?>> converters = List.of(
            new DefaultConverter<>(ZonedDateTime.class, Date.class) {
                @Override
                public Date toObject(ZonedDateTime zonedDateTime) {
                    return new Date(zonedDateTime.toInstant().toEpochMilli());
                }
            },
            new DefaultConverter<>(ZonedDateTime.class, String.class) {
                @Override
                public String toObject(ZonedDateTime zonedDateTime) {
                    return zonedDateTime.format(DateTimeFormatter.ISO_DATE_TIME);
                }
            }
        );

        public DateTimeContextVariableTypeConverter() {
            super(
                ZonedDateTime.class,
                (x) -> convert(x, ZonedDateTime.class),
                zonedDateTime -> zonedDateTime.format(DateTimeFormatter.ISO_DATE_TIME),
                promptString -> ZonedDateTime.parse(promptString, DateTimeFormatter.ISO_DATE_TIME),
                converters
            );
        }
    }

    public static void main(String[] args) {

        System.out.println("======== Method Function types ========");

        OpenAIAsyncClient client;

        if (USE_AZURE_CLIENT) {
            client = new OpenAIClientBuilder()
                    .credential(new AzureKeyCredential(CLIENT_KEY))
                    .endpoint(CLIENT_ENDPOINT)
                    .buildAsyncClient();
        } else {
            client = new OpenAIClientBuilder()
                    .credential(new KeyCredential(CLIENT_KEY))
                    .buildAsyncClient();
        }

        TextGenerationService textGenerationService = OpenAITextGenerationService.builder()
                .withOpenAIAsyncClient(client)
                .withModelId("text-davinci-003")
                .build();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        KernelPlugin plugin = KernelPluginFactory
            .createFromObject(new LocalExamplePlugin(), "Examples");

        KernelPlugin summarize = KernelPluginFactory
            .importPluginFromDirectory(
                Path.of("java/samples/sample-code/src/main/resources/Plugins"),
                "SummarizePlugin",
                null);

        KernelPlugin examplePlugin = KernelPluginFactory
            .importPluginFromResourcesDirectory(
                "Plugins",
                "ExamplePlugins",
                "ExampleFunction",
                null,
                Example09_FunctionTypes.class
            );

        Kernel kernel = Kernel.builder()
            .withDefaultAIService(TextGenerationService.class, textGenerationService)
            .withPlugin(plugin)
            .withPlugin(summarize)
            .withPlugin(examplePlugin)
            .build();

        // Different ways to invoke a function (not limited to these examples)
        kernel.invokeAsync(plugin.get("NoInputWithVoidResult"), null, String.class).block();
        kernel.invokeAsync(plugin.get("NoInputTaskWithVoidResult"), null, String.class).block();

        kernel
            .invokeAsync(
                plugin.get("InputDateTimeWithStringResult"),
                KernelArguments
                    .builder()
                    .withVariable("currentDate",
                        ContextVariable.of(
                            ZonedDateTime.now(),
                            new DateTimeContextVariableTypeConverter()
                        )
                    )
                    .build(),
                String.class
            ).block();

        kernel.invokeAsync(plugin.get("NoInputTaskWithStringResult"), null, String.class).block();

        kernel.invokeAsync(plugin.get("MultipleInputsWithVoidResult"),
                KernelArguments
                    .builder()
                    .withVariable("x", "x string")
                    .withVariable("y", 100)
                    .withVariable("z", 1.5)
                    .build(),
                String.class)
            .block();

        kernel
            .invokeAsync(plugin.get("ComplexInputWithStringResult"),
                KernelArguments
                    .builder()
                    .withVariable(
                        "complexObject",
                        ContextVariable.of(
                            new Object() {
                                @Override
                                public String toString() {
                                    return "A complex object";
                                }
                            },
                            new NoopConverter<>(Object.class)
                        )
                    )
                    .build(),
                String.class)
            .block();

        kernel
            .invokeAsync(plugin.get("InputStringTaskWithStringResult"),
                KernelArguments
                    .builder()
                    .withVariable("echoInput", "return this")
                    .build(),
                String.class)
            .block();

        kernel
            .invokeAsync(plugin.get("InputStringTaskWithVoidResult"),
                KernelArguments
                    .builder()
                    .withVariable("x", "x input")
                    .build(),
                Void.class)
            .block();

        kernel
            .invokeAsync(plugin.get("noInputComplexReturnTypeAsync"),
                null,
                Temporal.class)
            .block();

        kernel
            .invokeAsync(plugin.get("noInputComplexReturnType"),
                null,
                Temporal.class)
            .block();

        /*
        TODO: support FunctionResult
        kernel
            .invokeAsync(plugin.get("NoInputWithFunctionResult"),
                null,
                Void.class)
            .block();

         */

        /*
        TODO: support injection
        // Injecting Parameters Examples
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingKernelFunctionWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingLoggerWithNoResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingLoggerFactoryWithNoResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingCultureInfoOrIFormatProviderWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingCancellationTokenWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingServiceSelectorWithStringResult)]);
        await kernel.InvokeAsync(plugin[nameof(LocalExamplePlugin.TaskInjectingKernelWithInputTextAndStringResult)],
            new()
        {
                ["textToSummarize"] = @"C# is a modern, versatile language by Microsoft, blending the efficiency of C++
            with Visual Basic's simplicity. It's ideal for a wide range of applications,
            emphasizing type safety, modularity, and modern programming paradigms."
        });

         */

        // You can also use the kernel.Plugins collection to invoke a function
        kernel
            .invokeAsync(
                kernel.getPlugins()
                    .getFunction("Examples", "NoInputWithVoidResult"),
                null,
                Void.class)
            .block();
    }


    public static class LocalExamplePlugin {

        /// <summary>
        /// Example of using a void function with no input
        /// </summary>
        @DefineKernelFunction(name = "NoInputWithVoidResult")
        public void NoInputWithVoidResult() {
            System.out.println("Running this.NoInputWithVoidResult) -> No input");
        }

        /// <summary>
        /// Example of using a void task function with no input
        /// </summary>
        @DefineKernelFunction(name = "NoInputTaskWithVoidResult")
        public Mono<Void> NoInputTaskWithVoidResult() {
            return Mono.fromRunnable(
                () -> System.out.println("Running this.NoInputTaskWithVoidResult) -> No input"));
        }

        /// <summary>
        /// Example of using a function with a DateTime input and a string result
        /// </summary>
        @DefineKernelFunction(name = "InputDateTimeWithStringResult")
        public String InputDateTimeWithStringResult(
            @KernelFunctionParameter(
                name = "currentDate",
                description = "Current date time",
                type = ZonedDateTime.class
            )
            ZonedDateTime currentDate) {
            var result = currentDate.format(DateTimeFormatter.ISO_DATE_TIME);
            System.out.println(
                "Running {nameof(this.InputDateTimeWithStringResult)} -> [currentDate = {"
                    + currentDate + "}] -> result: {" + result + "}");
            return result;
        }

        /// <summary>
        /// Example of using a Task function with no input and a string result
        /// </summary>
        @DefineKernelFunction(name = "NoInputTaskWithStringResult")
        public Mono<String> NoInputTaskWithStringResult() {
            return Mono.fromCallable(() -> {
                var result = "string result";
                System.out.println(
                    "Running {nameof(this.NoInputTaskWithStringResult)} -> No input -> result: {"
                        + result + "}");
                return result;
            });
        }

        /// <summary>
        /// Example passing multiple parameters with multiple types
        /// </summary>
        @DefineKernelFunction(name = "MultipleInputsWithVoidResult")
        public void MultipleInputsWithVoidResult(
            @KernelFunctionParameter(
                name = "x"
            )
            String x,

            @KernelFunctionParameter(
                name = "y",
                type = int.class
            )
            int y,

            @KernelFunctionParameter(
                name = "z",
                type = double.class
            )
            double z) {
            System.out.println(
                "Running {nameof(this.MultipleInputsWithVoidResult)} -> input: [x = {" + x
                    + "}, y = {" + y + "}, z = {" + z + "}]");
        }

        /// <summary>
        /// Example passing a complex object and returning a string result
        /// </summary>
        @DefineKernelFunction(name = "ComplexInputWithStringResult")
        public String ComplexInputWithStringResult(
            @KernelFunctionParameter(
                name = "complexObject",
                type = Object.class
            )
            Object complexObject
        ) {
            String result = complexObject.toString();
            System.out.println(
                "Running {nameof(this.ComplexInputWithStringResult)} -> input: [complexObject = "
                    + complexObject + "] -> result: {"
                    + result + "}");
            return result;
        }


        /// <summary>
        /// Example using an async task function echoing the input
        /// </summary>
        @DefineKernelFunction(name = "InputStringTaskWithStringResult")
        public Mono<String> InputStringTaskWithStringResult(

            @KernelFunctionParameter(
                name = "echoInput"
            )
            String echoInput) {
            return Mono.fromCallable(() -> {
                System.out.println(
                    "Running {nameof(this.InputStringTaskWithStringResult)} -> input: [echoInput = "
                        + echoInput + "] -> result: {"
                        + echoInput + "}");
                return echoInput;
            });
        }

        /// <summary>
        /// Example using an async void task with string input
        /// </summary>
        @DefineKernelFunction(name = "InputStringTaskWithVoidResult")
        public Mono<Void> InputStringTaskWithVoidResult(
            @KernelFunctionParameter(
                name = "x"
            )
            String x) {
            return Mono.fromRunnable(() -> {
                System.out.println(
                    "Running {nameof(this.InputStringTaskWithVoidResult)} -> input: [x = {" + x
                        + "}]");
            });
        }

        @DefineKernelFunction(
            name = "noInputComplexReturnTypeAsync",
            returnType = "java.time.temporal.Temporal"
        )
        public Mono<LocalDateTime> noInputComplexReturnTypeAsync() {
            return Mono.just(
                LocalDateTime.now()
            );
        }


        @DefineKernelFunction(
            name = "noInputComplexReturnType",
            returnType = "java.time.temporal.Temporal"
        )
        public LocalDateTime noInputComplexReturnType() {
            return LocalDateTime.now();
        }

        /*
        /// <summary>
        /// Example using a function to return the result of another inner function
        /// </summary>
        @DefineKernelFunction(name = "InputStringTaskWithVoidResult")
        public FunctionResult NoInputWithFunctionResult()
        {
            var myInternalFunction = KernelFunctionFactory.CreateFromMethod(() => { });
            var result = new FunctionResult(myInternalFunction);
            Console.WriteLine($"Running {nameof(this.NoInputWithFunctionResult)} -> No input -> result: {result.GetType().Name}");
            return result;
        }
         */

        /*

        /// <summary>
        /// Example using a task function to return the result of another kernel function
        /// </summary>
    [KernelFunction]
        public async Task<FunctionResult> NoInputTaskWithFunctionResult(Kernel kernel)
    {
        var result = await kernel.InvokeAsync(kernel.Plugins["Examples"][nameof(this.NoInputWithVoidResult)]);
        Console.WriteLine($"Running {nameof(this.NoInputTaskWithFunctionResult)} -> Injected kernel -> result: {result.GetType().Name}");
        return result;
    }

        /// <summary>
        /// Example how to inject Kernel in your function
        /// This example uses the injected kernel to invoke a plugin from within another function
        /// </summary>
    [KernelFunction]
        public async Task<string> TaskInjectingKernelWithInputTextAndStringResult(Kernel kernel, string textToSummarize)
    {
        var summary = await kernel.InvokeAsync<string>(kernel.Plugins["SummarizePlugin"]["Summarize"], new() { ["input"] = textToSummarize });
        Console.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected kernel + input: [textToSummarize: {textToSummarize[..15]}...{textToSummarize[^15..]}] -> result: {summary}");
        return summary!;
    }

        /// <summary>
        /// Example how to inject the executing KernelFunction as a parameter
        /// </summary>
    [KernelFunction, Description("Example function injecting itself as a parameter")]
        public async Task<string> TaskInjectingKernelFunctionWithStringResult(KernelFunction executingFunction)
    {
        var result = $"Name: {executingFunction.Name}, Description: {executingFunction.Description}";
        Console.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Function -> result: {result}");
        return result;
    }

        /// <summary>
        /// Example how to inject ILogger in your function
        /// </summary>
    [KernelFunction]
        public Task TaskInjectingLoggerWithNoResult(ILogger logger)
        {
            logger.LogWarning("Running {FunctionName} -> Injected Logger", nameof(this.TaskInjectingLoggerWithNoResult));
            Console.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Logger");
            return Task.CompletedTask;
        }

        /// <summary>
        /// Example how to inject ILoggerFactory in your function
        /// </summary>
    [KernelFunction]
        public Task TaskInjectingLoggerFactoryWithNoResult(ILoggerFactory loggerFactory)
        {
            loggerFactory
                .CreateLogger<LocalExamplePlugin>()
            .LogWarning("Running {FunctionName} -> Injected Logger", nameof(this.TaskInjectingLoggerWithNoResult));

            Console.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Logger");
            return Task.CompletedTask;
        }

        /// <summary>
        /// Example how to inject a service selector in your function and use a specific service
        /// </summary>
    [KernelFunction]
        public async Task<string> TaskInjectingServiceSelectorWithStringResult(Kernel kernel, KernelFunction function, KernelArguments arguments, IAIServiceSelector serviceSelector)
    {
        ChatMessageContent? chatMessageContent = null;
        if (serviceSelector.TrySelectAIService<IChatCompletionService>(kernel, function, arguments, out var chatCompletion, out var executionSettings))
        {
            chatMessageContent = await chatCompletion.GetChatMessageContentAsync(new ChatHistory("How much is 5 + 5 ?"), executionSettings);
        }

        var result = chatMessageContent?.Content;
        Console.WriteLine($"Running {nameof(this.TaskInjectingKernelWithInputTextAndStringResult)} -> Injected Kernel, KernelFunction, KernelArguments, Service Selector -> result: {result}");
        return result ?? string.Empty;
    }

        /// <summary>
        /// Example how to inject CultureInfo or IFormatProvider in your function
        /// </summary>
        public async Task<string> TaskInjectingCultureInfoOrIFormatProviderWithStringResult(CultureInfo cultureInfo, IFormatProvider formatProvider)
    {
        var result = $"Culture Name: {cultureInfo.Name}, FormatProvider Equals CultureInfo?: {formatProvider.Equals(cultureInfo)}";
        Console.WriteLine($"Running {nameof(this.TaskInjectingCultureInfoOrIFormatProviderWithStringResult)} -> Injected CultureInfo, IFormatProvider -> result: {result}");
        return result;
    }

        /// <summary>
        /// Example how to inject current CancellationToken in your function
        /// </summary>
    [KernelFunction]
        public async Task<string> TaskInjectingCancellationTokenWithStringResult(CancellationToken cancellationToken)
    {
        var result = $"Cancellation resquested: {cancellationToken.IsCancellationRequested}";
        Console.WriteLine($"Running {nameof(this.TaskInjectingCultureInfoOrIFormatProviderWithStringResult)} -> Injected Cancellation Token -> result: {result}");
        return result;
    }

        public override string ToString()
    {
        return "Complex type result ToString override";
    }

         */
    }
}
