// Copyright (c) Microsoft. All rights reserved.
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.implementation.EmbeddedResourceLoader;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.samples.openapi.SemanticKernelOpenAPIImporter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import java.io.FileNotFoundException;

public class ExampleAdoptiumImporter {

    public static void main(String[] args) throws FileNotFoundException {
        runJson();
        runYaml();
    }

    private static void runJson() throws FileNotFoundException {
        String json = EmbeddedResourceLoader.readFile("adoptium.json",
            ExampleAdoptiumImporter.class);
        makeRequests(json);
    }

    private static void runYaml() throws FileNotFoundException {
        String yaml = EmbeddedResourceLoader.readFile("adoptium.yaml",
            ExampleAdoptiumImporter.class);
        makeRequests(yaml);
    }

    private static void makeRequests(String schema) {
        KernelPlugin plugin = SemanticKernelOpenAPIImporter
            .builder()
            .withPluginName("adoptium")
            .withSchema(schema)
            .build();

        Kernel kernel = ExampleOpenAPIParent.kernelBuilder()
            .withPlugin(plugin)
            .build();

        performRequest(kernel,
            """
                Parse the java version 11.0.22+9?
                """);

        performRequest(kernel,
            """
                What are the names of the GA versions of Java available between 8 and 9 inclusive?
                """);

        performRequest(kernel,
            """
                What is the version of the latest GA release of Java between 11 and 12?
                """);
    }

    private static void performRequest(Kernel kernel, String request) {
        KernelFunction<String> function = KernelFunction.<String>createFromPrompt(request)
            .build();

        FunctionResult<String> result = kernel.invokeAsync(function)
            .withResultType(String.class)
            .withToolCallBehavior(ToolCallBehavior.allowAllKernelFunctions(true))
            .block();

        System.out.println(result.getResult());
    }

}
