// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.microsoft.semantickernel.aiservices.AIService;

/** Interface for text embedding generation services */
public interface TextEmbeddingGeneration extends EmbeddingGeneration<String>, AIService {
<<<<<<< AI
    interface Builder extends EmbeddingGeneration.Builder<String, TextEmbeddingGeneration> {}
      interface Builder extends EmbeddingGeneration.Builder<String, TextEmbeddingGeneration> {
      }
=======
<<<<<<< HEAD
    interface Builder extends EmbeddingGeneration.Builder<String, TextEmbeddingGeneration> {}
=======
      interface Builder extends EmbeddingGeneration.Builder<String, TextEmbeddingGeneration> {
      }
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
}
