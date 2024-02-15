package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.plugin.annotations.DefineKernelFunction;
import reactor.core.publisher.Mono;

public class Example60_AdvancedMethodFunctions {

    public static void main(String[] args) {
        System.out.println("======== Example60_AdvancedMethodFunctions ========");

        var kernel = Kernel.builder().build();

        System.out.println("Running Method Function Chaining example...");

        var functions = KernelPluginFactory.createFromObject(
            new FunctionsChainingPlugin(),
            FunctionsChainingPlugin.PluginName);

        kernel.addPlugin(functions);

        ContextVariableTypeConverter<MyCustomType> type = new ContextVariableTypeConverter<>(
            MyCustomType.class,
            o -> (MyCustomType) o,
            o -> o.text + " " + o.number,
            s -> null
        );

        ContextVariableTypes.addGlobalConverter(type);

        var result = kernel
            .invokeAsync(FunctionsChainingPlugin.PluginName, "Function1")
            .withArguments(
                KernelFunctionArguments
                    .builder()
                    .build())
            .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(MyCustomType.class))
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
                .invokeAsync(PluginName, "Function2")
                .withArguments(KernelFunctionArguments.builder().build())
                .withResultType(ContextVariableTypes.getGlobalVariableTypeForClass(
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
}
