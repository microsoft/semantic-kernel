// Copyright (c) Microsoft. All rights reserved.

import { IChatMessage } from './ChatMessage';

export interface Bot {
    Schema: { Name: string; Version: number };
    Configurations: { EmbeddingAIService: string; EmbeddingDeploymentOrModelId: string };
    ChatTitle: string;
    ChatHistory: IChatMessage[];
    Embeddings: any[]; // TODO: type this
}
