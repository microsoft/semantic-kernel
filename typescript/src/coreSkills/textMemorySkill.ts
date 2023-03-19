// Copyright (c) Microsoft. All rights reserved.

import { SKContext } from '../orchestration';

/**
 * TextMemorySkill provides a skill to save or recall information from the long or short term memory.
 *
 * Usage: kernel.ImportSkill("memory", new TextMemorySkill());
 * Examples:
 * SKContext["input"] = "what is the capital of France?"
 * {{memory.recall $input }} => "Paris"
 */
export class TextMemorySkill {
    private defaultCollection: string = 'generic';
    private defaultRelevance: string = '0.75';

    // Name of the context variable used to specify which memory collection to use.
    public collectionParam: string = 'collection';

    // Name of the context variable used to specify memory search relevance score.
    public relevanceParam: string = 'relevance';

    // Name of the context variable used to specify a unique key associated with stored information.
    public keyParam: string = 'key';

    /**
     * Recall a fact from the long term memory
     *
     * Examples:
     * SKContext["input"] = "what is the capital of France?"
     * {{memory.recall $input }} => "Paris"
     *
     * @param ask - The information to retrieve
     * @param context - Contains the 'collection' to search for information and 'relevance' score
     * @returns Returns a promise that resolves to the memory text, or an empty string if not found
     */
    public async recall(ask: string, context: SKContext): Promise<string> {
        const collection = context.variables;
        if (!collection) {
            throw 'Memory collection not defined';
        }

        let relevance = context.relevance || DefaultRelevance;

        console.log(`Searching memory for "${ask}", collection "${collection}", relevance "${relevance}"`);

        let memory = await context.memory.search(collection, ask, {
            limit: 1,
            minRelevanceScore: parseFloat(relevance),
        });

        if (!memory) {
            console.log(`Memory not found in collection: ${collection}`);
        } else {
            console.log(`Memory found (collection: ${collection})`);
        }

        return memory ? memory.text : '';
    }

    /**
     * Save information to semantic memory.
     *
     * Examples:
     * SKContext["input"] = "the capital of France is Paris";
     * SKContext[TextMemorySkill.KeyParam] = "countryInfo1";
     * {{memory.save $input }}
     *
     * @param text - The information to save.
     * @param context - Contains the 'collection' to save the information and unique 'key' to associate it with.
     */
    public async save(text: string, context: SKContext): Promise<void> {
        let collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        if (!collection) {
            throw new Error('Memory collection not defined');
        }
        let key = context.Variables.ContainsKey(KeyParam) ? context[KeyParam] : '';
        if (!key) {
            throw new Error('Memory key not defined');
        }

        context.Log.LogTrace("Saving memory to collection '{0}'", collection);

        await context.Memory.SaveInformationAsync(collection, text, key);
    }
}
