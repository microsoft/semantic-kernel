// Copyright (c) Microsoft. All rights reserved.

/**
 * Copy of metadata associated with a memory entry.
 */
export class MemoryQueryResult {
    // Whether the source data used to calculate embeddings are stored in the local
    // storage provider or is available through and external service, such as web site, MS Graph, etc.
    public readonly isReference: boolean;

    // A value used to understand which external service owns the data, to avoid storing the information
    // inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
    public readonly externalSourceName: string;

    // Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
    public readonly id: string;

    // Optional entry description, useful for external references when Text is empty.
    public readonly description: string;

    // Source text, available only when the memory is not an external source.
    public readonly text: string;

    // Search relevance, from 0 to 1, where 1 means perfect match.
    public readonly relevance: number;

    /**
     * Create new instance of MemoryQueryResult.
     *
     * @constructor
     * @param isReference Whether the source data used to calculate embeddings are stored in the local storage provider or is available through and external service, such as web site, MS Graph, etc.
     * @param sourceName A value used to understand which external service owns the data, to avoid storing the information inside the Id. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
     * @param id Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
     * @param description Optional title describing the entry, useful for external references when Text is empty.
     * @param text Source text, available only when the memory is not an external source.
     * @param relevance Search relevance, from 0 to 1, where 1 means perfect match.
     */
    public constructor(
        isReference: boolean,
        sourceName: string,
        id: string,
        description: string,
        text: string,
        relevance: number
    ) {
        this.isReference = isReference;
        this.externalSourceName = sourceName;
        this.id = id;
        this.description = description;
        this.text = text;
        this.relevance = relevance;
    }
}
