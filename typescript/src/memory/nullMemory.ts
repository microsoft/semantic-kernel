// Copyright (c) Microsoft. All rights reserved.

import { ISemanticTextMemory } from './iSemanticTextMemory';
import { MemoryQueryResult } from './memoryQueryResult';

/**
 * Implementation of {@link ISemanticTextMemory} that stores nothing.
 */
export class NullMemory implements ISemanticTextMemory {
    // Singleton instance.
    public static readonly instance = new NullMemory();

    /**
     * @inheritdoc
     */
    public async saveInformation(
        _collection: string,
        _text: string,
        _id: string,
        _description?: string
    ): Promise<void> {
        // NoOp
    }

    /**
     * @inheritdoc
     */
    public async saveReference(
        _collection: string,
        _text: string,
        _externalId: string,
        _externalSourceName: string,
        _description?: string
    ): Promise<void> {
        // NoOp
    }

    /**
     * @inheritdoc
     */
    public async get(_collection: string, _key: string): Promise<MemoryQueryResult | undefined> {
        return;
    }

    /**
     * @inheritdoc
     */
    public async search(
        _collection: string,
        _query: string,
        _limit: number,
        _minRelevanceScore: number
    ): Promise<MemoryQueryResult[]> {
        return [];
    }

    /**
     * @inheritdoc
     */
    public async getCollections(): Promise<string[]> {
        return [];
    }
}
