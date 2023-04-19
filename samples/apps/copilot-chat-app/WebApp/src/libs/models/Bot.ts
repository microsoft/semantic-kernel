// Copyright (c) Microsoft. All rights reserved.

import { ChatMessage } from './ChatMessage';

export interface Bot {
    Schema: { Name: string; Version: number };
    Configurations: { EmbeddingAIService: string; EmbeddingDeploymentOrModelId: string };
    ChatTitle: string;
    ChatHistory: ChatMessage[];
    Embeddings: any[]; // TODO: type this
}
