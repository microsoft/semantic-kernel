// Copyright (c) Microsoft. All rights reserved.

import { MemoryQueryResult } from './memoryQueryResult';

/**
 * An interface for semantic memory that creates and recalls memories associated with text.
 */
export interface ISemanticTextMemory {
    /**
     * Save some information into the semantic memory, keeping only a reference to the source information.
     *
     * @param collection Collection where to save the information.
     * @param text Information to save.
     * @param id Unique identifier.
     * @param description Optional description.
     */
    saveInformation(collection: string, text: string, id: string, description?: string): Promise<void>;

    /**
     * Save some information into the semantic memory, keeping only a reference to the source information.
     *
     * @param collection Collection where to save the information.
     * @param text Information to save.
     * @param externalId Unique identifier, e.g. URL or GUID to the original source.
     * @param externalSourceName Name of the external service, e.g. "MSTeams", "GitHub", "WebSite", "Outlook IMAP", etc.
     * @param description Optional description.
     */
    saveReference(
        collection: string,
        text: string,
        externalId: string,
        externalSourceName: string,
        description?: string
    ): Promise<void>;

    /**
     * Fetch a memory by key.
     * For local memories the key is the "id" used when saving the record.
     * For external reference, the key is the "URI" used when saving the record.
     *
     * @param collection Collection to search.
     * @param key Unique memory record identifier.
     * @returns Memory record, or null when nothing is found.
     */
    get(collection: string, key: string): Promise<MemoryQueryResult | undefined>;

    /**
     * Find some information in memory.
     *
     * @param collection Collection to search.
     * @param query What to search for.
     * @param limit How many results to return.
     * @param minRelevanceScore Minimum relevance score, from 0 to 1, where 1 means exact match.
     * @returns Memories found.
     */
    search(collection: string, query: string, limit: number, minRelevanceScore: number): Promise<MemoryQueryResult[]>;
}
