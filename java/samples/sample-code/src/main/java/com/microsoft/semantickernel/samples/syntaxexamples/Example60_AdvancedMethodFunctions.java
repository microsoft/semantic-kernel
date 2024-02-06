package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import reactor.core.publisher.Mono;

public class Example60_AdvancedMethodFunctions {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) {
        System.out.println("======== Example58_ConfigureExecutionSettings ========");

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

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .build();

        System.out.println("Running Method Function Chaining example...");

        var functions = KernelPluginFactory.createFromObject(
            new FunctionsChainingPlugin(),
            FunctionsChainingPlugin.PluginName);

        kernel.getPlugins().add(functions);

        ContextVariableTypeConverter<MyCustomType> type = new ContextVariableTypeConverter<>(
            MyCustomType.class,
            o -> (MyCustomType) o,
            o -> o.text + " " + o.number,
            s -> null
        );

        ContextVariableTypes.DEFAULT_TYPES.putConverter(type);

        var result = kernel
            .invokeAsync(
                FunctionsChainingPlugin.PluginName,
                "Function1",
                KernelFunctionArguments
                    .builder()
                    .build(),
                ContextVariableTypes.getDefaultVariableTypeForClass(MyCustomType.class)
            )
            .block();

        System.out.println("CustomType.Number: " + result.getResult().number); // 2
        System.out.println(
            "CustomType.Text: " + result.getResult().text); // From Function1 + From Function2

    }


    /// <summary>
    /// In order to use custom types, <see cref="TypeConverter"/> should be specified,
    /// that will convert object instance to string representation.
    /// </summary>
    /// <remarks>
    /// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
    /// it can be passed to AI for further processing using prompt functions.
    /// It's possible to choose any format (e.g. XML, JSON, YAML) to represent your object.
    /// </remarks>
    public static class MyCustomType {

        public int number;
        public String text;

        public MyCustomType(int i, String text) {
            this.number = i;
            this.text = text;
        }
    }

    /// <summary>
    /// Plugin example with two method functions, where one function is called from another.
    /// </summary>

    public static class FunctionsChainingPlugin {

        public static final String PluginName = "FunctionsChainingPlugin";


        @DefineKernelFunction(
            name = "Function1",
            returnType = "com.microsoft.semantickernel.samples.syntaxexamples.Example60_AdvancedMethodFunctions$MyCustomType")
        public Mono<MyCustomType> function1Async(Kernel kernel) {
            // Execute another function
            return kernel
                .invokeAsync(
                    PluginName,
                    "Function2",
                    KernelFunctionArguments.builder().build(),
                    ContextVariableTypes.getDefaultVariableTypeForClass(
                        Example60_AdvancedMethodFunctions.MyCustomType.class))
                .flatMap(value -> {
                    // Process the result
                    return Mono.just(
                        new MyCustomType(
                            2 * value.getResult().number,
                            "From Function1 + " + value.getResult().text));
                });
        }

        @DefineKernelFunction(
            name = "Function2",
            returnType = "com.microsoft.semantickernel.samples.syntaxexamples.Example60_AdvancedMethodFunctions$MyCustomType")
        public MyCustomType function2() {
            return new MyCustomType(1, "From Function2");
        }
    }
    /*

    public static async Task RunAsync()
    {
        await MethodFunctionsChainingAsync();
    }

    #region Method Functions Chaining

    /// <summary>
    /// This example executes Function1, which in turn executes Function2.
    /// </summary>
    private static async Task MethodFunctionsChainingAsync()
    {
        Console.WriteLine("Running Method Function Chaining example...");

        var kernel = new Kernel();

        var functions = kernel.ImportPluginFromType<FunctionsChainingPlugin>();

        var customType = await kernel.InvokeAsync<MyCustomType>(functions["Function1"]);

        Console.WriteLine($"CustomType.Number: {customType!.Number}"); // 2
        Console.WriteLine($"CustomType.Text: {customType.Text}"); // From Function1 + From Function2
    }

    #endregion

    #region Custom Type

    /// <summary>
    /// In order to use custom types, <see cref="TypeConverter"/> should be specified,
    /// that will convert object instance to string representation.
    /// </summary>
    /// <remarks>
    /// <see cref="TypeConverter"/> is used to represent complex object as meaningful string, so
    /// it can be passed to AI for further processing using prompt functions.
    /// It's possible to choose any format (e.g. XML, JSON, YAML) to represent your object.
    /// </remarks>
    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Number { get; set; }

        public string? Text { get; set; }
    }

    /// <summary>
    /// Implementation of <see cref="TypeConverter"/> for <see cref="MyCustomType"/>.
    /// In this example, object instance is serialized with <see cref="JsonSerializer"/> from System.Text.Json,
    /// but it's possible to convert object to string using any other serialization logic.
    /// </summary>
    private sealed class MyCustomTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) => true;

        /// <summary>
        /// This method is used to convert object from string to actual type. This will allow to pass object to
        /// method function which requires it.
        /// </summary>
        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value)
        {
            return JsonSerializer.Deserialize<MyCustomType>((string)value);
        }

        /// <summary>
        /// This method is used to convert actual type to string representation, so it can be passed to AI
        /// for further processing.
        /// </summary>
        public override object? ConvertTo(ITypeDescriptorContext? context, CultureInfo? culture, object? value, Type destinationType)
        {
            return JsonSerializer.Serialize(value);
        }
    }
     */
}
