package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.textcompletion.OpenAITextGenerationService;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter.NoopConverter;
import static com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes.convert;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.plugin.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;

import java.nio.file.Path;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.Temporal;
import java.util.Date;
import java.util.List;
import java.util.concurrent.CountDownLatch;

import reactor.core.publisher.Mono;

public class Example09_FunctionTypes {

    private static final String PLUGIN_DIR =
        System.getenv("PLUGIN_DIR") == null ? "." : System.getenv("PLUGIN_DIR");
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "text-davinci-003");


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
                (x) -> {
                    if (x instanceof OffsetDateTime) {
                        return ((OffsetDateTime) x).toZonedDateTime();
                    }
                    return convert(x, ZonedDateTime.class);
                },
                zonedDateTime -> zonedDateTime.format(DateTimeFormatter.ISO_DATE_TIME),
                promptString -> ZonedDateTime.parse(promptString, DateTimeFormatter.ISO_DATE_TIME),
                converters
            );
        }
    }

    public static void main(String[] args) throws InterruptedException {

        System.out.println("======== Method Function types ========");

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

        TextGenerationService textGenerationService = OpenAITextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        // Load native plugin into the kernel function collection, sharing its functions with prompt templates
        KernelPlugin plugin = KernelPluginFactory
            .createFromObject(new LocalExamplePlugin(), "Examples");

        KernelPlugin summarize = KernelPluginFactory
            .importPluginFromDirectory(
                Path.of(PLUGIN_DIR, "java/samples/sample-code/src/main/resources/Plugins"),
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
            .withAIService(TextGenerationService.class, textGenerationService)
            .withPlugin(plugin)
            .withPlugin(summarize)
            .withPlugin(examplePlugin)
            .build();

        // Different ways to invoke a function (not limited to these examples)
        FunctionResult<?> result = kernel.invokeAsync(plugin.get("NoInputWithVoidResult"))
            .block();
        assert result == null;

        CountDownLatch cdl = new CountDownLatch(1);

        kernel
            .invokeAsync(plugin.get("NoInputWithVoidResult"))
            .doFinally(ignore -> cdl.countDown())
            .subscribe(ignore -> {
                throw new RuntimeException("No return expected");
            });

        cdl.await();

        System.out.println(result != null ? result.getResult() : "null");
        result = kernel.invokeAsync(plugin.get("NoInputTaskWithVoidResult"))
            .block();
        assert result == null;
        System.out.println(result != null ? result.getResult() : "null");

        result = kernel
            .invokeAsync(plugin.<String>get("InputDateTimeWithStringResult"))
            .withArguments(
                KernelFunctionArguments
                    .builder()
                    .withVariable("currentDate",
                        ContextVariable.of(
                            ZonedDateTime.of(1, 1, 1, 1, 1, 1, 1, ZoneOffset.UTC),
                            new DateTimeContextVariableTypeConverter()
                        )
                    )
                    .build()
            ).block();
        System.out.println(result.getResult());

        result = kernel.invokeAsync(plugin.<String>get("NoInputTaskWithStringResult"))
            .block();
        System.out.println(result.getResult());

        kernel.invokeAsync(plugin.<String>get("MultipleInputsWithVoidResult"))
            .withArguments(
                KernelFunctionArguments
                    .builder()
                    .withVariable("x", "x string")
                    .withVariable("y", 100)
                    .withVariable("z", 1.5)
                    .build())
            .block();
        System.out.println(result.getResult());

        result = kernel
            .invokeAsync(plugin.<String>get("ComplexInputWithStringResult"))
            .withArguments(
                KernelFunctionArguments
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
                    .build())
            .block();
        System.out.println(result.getResult());

        result = kernel
            .invokeAsync(plugin.<String>get("InputStringTaskWithStringResult"))
            .withArguments(
                KernelFunctionArguments
                    .builder()
                    .withVariable("echoInput", "return this")
                    .build())
            .block();
        System.out.println(result.getResult());

        result = kernel
            .invokeAsync(plugin.<String>get("InputStringTaskWithVoidResult"))
            .withArguments(
                KernelFunctionArguments
                    .builder()
                    .withVariable("x", "x input")
                    .build()
            )
            .block();
        assert result == null;
        System.out.println(result != null ? result.getResult() : "null");

        result = kernel
            .invokeAsync(plugin.<String>get("noInputComplexReturnTypeAsync"))
            .block();
        System.out.println(result.getResult());

        var temporalResult = kernel
            .invokeAsync(plugin.<Temporal>get("noInputComplexReturnType"))
            .block();
        System.out.println(temporalResult.getResult());

        // Possibilities for return type combinations:
        // | Method return type | Declared Function Return Type | Invocation Return type |
        // |--------------------|-------------------------------|------------------------|
        // | T                  | T                             | T                      |
        // | T                  | T                             | V converted from T     |

        // | T                  | U extends T                   | T                      |
        // | T                  | U extends T                   | U                      |
        // | T                  | U extends T                   | V converted from U     |

        var result1 = kernel
            .invokeAsync(plugin.<OffsetDateTime>get("conversionScenarioA"))
            .block();
        System.out.println(result1.getResult());

        var result2 = kernel
            .invokeAsync(plugin.<Instant>get("conversionScenarioA"))
            .block();
        System.out.println(result2.getResult());

        var result3 = kernel
            .invokeAsync(plugin.<OffsetDateTime>get("conversionScenarioB"))
            .block();
        System.out.println(result3.getResult());

        var result4 = kernel
            .invokeAsync(plugin.<Temporal>get("conversionScenarioB"))
            .block();
        System.out.println(result4.getResult());

        var result5 = kernel
            .invokeAsync(plugin.<Instant>get("conversionScenarioB"))
            .block();
        System.out.println(result5.getResult());

        var result6 = kernel
            .invokeAsync(plugin.get("noInputComplexReturnType"))
            .block();
        System.out.println(result6.getResult());

        var result7 = kernel
            .invokeAsync(plugin.get("withDefaultValue"))
            .block();
        System.out.println(result7.getResult());

        var result8 = kernel
            .invokeAsync(plugin.get("noInputComplexReturnType"))
            .withResultType(
                new ContextVariableType<>(
                    new DateTimeContextVariableTypeConverter(),
                    ZonedDateTime.class)
            )
            .block();
        System.out.println(result8.getResult());

        var result9 = kernel
            .invokeAsync(plugin.get("noInputComplexReturnType"))
            .withResultType(
                new ContextVariableType<>(
                    new DateTimeContextVariableTypeConverter(),
                    ZonedDateTime.class)
            )
            .block();
        System.out.println(result9.getResult());

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
                kernel.getFunction("Examples", "NoInputWithVoidResult"))
            .block();
    }


    public static class LocalExamplePlugin {

        /// <summary>
        /// Example of using a void function with no input
        /// </summary>
        @DefineKernelFunction(name = "NoInputWithVoidResult", returnType = "void")
        public void NoInputWithVoidResult() {
            System.out.println("Running this.NoInputWithVoidResult) -> No input");
        }

        /// <summary>
        /// Example of using a void task function with no input
        /// </summary>
        @DefineKernelFunction(
            name = "NoInputTaskWithVoidResult",
            returnType = "java.lang.Void"
        )
        public Mono<Void> NoInputTaskWithVoidResult() {
            return Mono.fromRunnable(
                () -> System.out.println("Running this.NoInputTaskWithVoidResult) -> No input"));
        }

        /// <summary>
        /// Example of using a function with a DateTime input and a string result
        /// </summary>
        @DefineKernelFunction(
            name = "InputDateTimeWithStringResult",
            returnType = "java.lang.String")
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
        @DefineKernelFunction(
            name = "NoInputTaskWithStringResult",
            returnType = "java.lang.String")
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
        @DefineKernelFunction(
            name = "InputStringTaskWithStringResult",
            returnType = "java.lang.String"
        )
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
        @DefineKernelFunction(
            name = "InputStringTaskWithVoidResult",
            returnType = "java.lang.Void"
        )
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
        public Mono<OffsetDateTime> noInputComplexReturnTypeAsync() {
            return Mono.just(
                OffsetDateTime.of(1, 1, 1, 1, 1, 1, 1, ZoneOffset.UTC)
            );
        }

        @DefineKernelFunction(
            name = "noInputComplexReturnType",
            returnType = "java.time.temporal.Temporal"
        )
        public OffsetDateTime noInputComplexReturnType() {
            return OffsetDateTime.of(1, 1, 1, 1, 1, 1, 1, ZoneOffset.UTC);
        }

        @DefineKernelFunction(
            name = "withDefaultValue",
            returnType = "java.lang.String"
        )
        public String withDefaultValue(
            @KernelFunctionParameter(
                name = "x",
                defaultValue = "1",
                type = int.class
            )
            int x
        ) {
            return Integer.toString(x);
        }

        // Possibilities for return type combinations:
        // | Method return type | Declared Function Return Type |
        // |--------------------|-------------------------------|
        // | T                  | T                             |
        // | T                  | U extends T                   |
        @DefineKernelFunction(
            name = "conversionScenarioA",
            returnType = "java.time.OffsetDateTime"
        )
        public OffsetDateTime conversionScenarioA() {
            return OffsetDateTime.of(1, 1, 1, 1, 1, 1, 1, ZoneOffset.UTC);
        }

        @DefineKernelFunction(
            name = "conversionScenarioB",
            returnType = "java.time.temporal.Temporal"
        )
        public OffsetDateTime conversionScenarioB() {
            return OffsetDateTime.of(1, 1, 1, 1, 1, 1, 1, ZoneOffset.UTC);
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
