// Copyright (c) Microsoft. All rights reserved.
import com.azure.core.http.HttpHeader;
import com.azure.core.http.HttpHeaders;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.implementation.EmbeddedResourceLoader;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.samples.openapi.SemanticKernelOpenAPIImporter;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Assertions;

public class ExampleAuthenticatedRequestImporter {

    public static void main(String[] args) throws IOException {

        String yaml = EmbeddedResourceLoader.readFile("authenticatedRequest.yaml",
            ExampleAuthenticatedRequestImporter.class);

        KernelPlugin plugin = SemanticKernelOpenAPIImporter
            .builder()
            .withPluginName("authenticatedRequest")
            .withSchema(yaml)
            .withServer("http://127.0.0.1:8890")
            .withHttpHeaders(new HttpHeaders(List.of(
                new HttpHeader("Authorization", "Bearer 1234"))))
            .build();

        Kernel kernel = ExampleOpenAPIParent.kernelBuilder()
            .withPlugin(plugin)
            .build();
        HttpServer httpServer = null;
        try {
            httpServer = HttpServer.create(new InetSocketAddress("127.0.0.1", 8890), 0);
            httpServer.createContext("/state", exchange -> {

                Assertions.assertTrue(
                    exchange.getRequestHeaders().containsKey("Authorization"),
                    "Authorization header not found");

                exchange.sendResponseHeaders(HttpURLConnection.HTTP_OK, 0);
                exchange.getResponseBody().write(
                    """
                        {
                            "state": "running"
                        }
                        """
                        .stripIndent()
                        .getBytes(StandardCharsets.UTF_8));
                exchange.close();
            });
            httpServer.start();

            performRequest(kernel,
                """
                    What is the current state of the system?
                    """.stripIndent());

        } finally {
            httpServer.stop(0);
        }

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
