// Copyright (c) Microsoft. All rights reserved.
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.implementation.EmbeddedResourceLoader;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.samples.openapi.SemanticKernelOpenAPIImporter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import java.io.FileNotFoundException;

public class ExamplePetstoreImporter {

    public static void main(String[] args) throws FileNotFoundException {

        String yaml = EmbeddedResourceLoader.readFile("petstore.yaml",
            ExamplePetstoreImporter.class);

        KernelPlugin plugin = SemanticKernelOpenAPIImporter
            .builder()
            .withPluginName("petstore")
            .withSchema(yaml)
            .withServer("http://localhost:8090/api/v3")
            .build();

        Kernel kernel = ExampleOpenAPIParent.kernelBuilder()
            .withPlugin(plugin)
            .build();

        performRequest(kernel,
            """
                Create a user with the following details:
                username: john_doe
                first name: John
                last name: Doe
                email: john_doe@example.com
                password: password123
                phone: 1234567890
                user status: 1""");
        performRequest(kernel, "Add a new cat called Sandy to the store.");
        performRequest(kernel, "List all available pets.");

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
