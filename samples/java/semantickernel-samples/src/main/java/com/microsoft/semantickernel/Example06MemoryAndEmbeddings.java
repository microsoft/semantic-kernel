package com.microsoft.semantickernel;

import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.builders.SKBuilders;
import java.io.IOException;

public class Example06MemoryAndEmbeddings {

  public static Kernel getKernel(OpenAIAsyncClient client) {
    KernelConfig config = SKBuilders.kernelConfig()
        .addTextCompletionService("davinci", kernel -> SKBuilders.textCompletionService().build(client, "text-davinci-003"))
        .addTextCompletionService("embeddings", kernel -> SKBuilders.textCompletionService().build(client, "text-embedding-ada-002"))
        .build();

    // TODO: Add Volatile memory

    Kernel kernel = SKBuilders.kernel()
        .setKernelConfig(config)
        .build();

    return kernel;
  }

  public static void run (boolean useAzureOpenAI) {
    OpenAIAsyncClient client = Example00GettingStarted.getClient(useAzureOpenAI);
    Kernel kernel = getKernel(client);
  }

  public static void main(String[] args) {
    run(false);
  }
}
