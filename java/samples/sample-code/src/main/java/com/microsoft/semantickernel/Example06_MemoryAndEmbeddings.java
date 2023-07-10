package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.builders.SKBuilders;

import java.io.IOException;

public class Example06_MemoryAndEmbeddings {

  public static Kernel getKernel(OpenAIAsyncClient client) {
    KernelConfig config = SKBuilders.kernelConfig()
        .addTextCompletionService(
            "davinci", kernel -> SKBuilders.textCompletionService().build(client, "text-davinci-003"))
       .build();

    // TODO: Add Volatile memory

    Kernel kernel = SKBuilders.kernel()
        .withKernelConfig(config)
        .build();

    return kernel;
  }

  public static void run(Config.ClientType clientType) throws IOException {
    Kernel kernel = getKernel(clientType.getClient());
  }

  public static void main(String[] args) throws IOException {
    // Send one of Config.ClientType.OPEN_AI or Config.ClientType.AZURE_OPEN_AI
    run(Config.ClientType.OPEN_AI);
  }
}
