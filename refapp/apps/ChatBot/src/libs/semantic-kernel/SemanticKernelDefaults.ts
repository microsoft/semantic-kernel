// Copyright (c) Microsoft. All rights reserved.

export const SemanticKernelDefaults = {
    debug: {
        root: 'sk',
    },
    models: {
        tokens: {
            estimatorFactor: 2.5,
        },
        embedding: {
            model: 'text-embedding-ada-002',
            maxTokens: 2048,
        },
        completion: {
            maxTokens: 8192,
        },
    },
    agents: {
        bot: {
            defaultConfig: {
                responseContextWeights: {
                    memories: {
                        weight: 0.3,
                        isLimit: true,
                    },
                    documents: {
                        weight: 0.3,
                        isLimit: true,
                    },
                    relatedHistory: {
                        weight: 0.3,
                        isLimit: true,
                    },
                    recentHistory: {
                        weight: 0.25,
                        isLimit: false,
                    },
                },
            },
            knowledgeCutoffDate: '1/1/2022',
            cognitiveMemory: {
                similarityThreshold: 0.7,
                eventIntervalMs: 60 * 1000,
            },
            response: {
                botTypingStartDelayMs: 2000,
                botTypingStartSignal: 'bot-typing-start',
                botTypingStopSignal: 'bot-typing-stop',
                similarityLimit: 1000,
                similarityThreshold: 0.8,
                maxRetries: 5,
                temperature: 0.7,
                topP: 1,
                frequencyPenalty: 0.5,
                presencePenalty: 0.5,
            },
            models: {
                completion: {
                    tokenLimits: {
                        response: 1024,
                    },
                },
            },
            storageType: 'fluid',
            // storageType: 'localStorage',
            newChatTitle: 'My Chat',
        },
        documentHub: {
            storageType: 'fluid',
        },
    },
    memory: {
        prompts: {
            merge: 'Merge the following {{memory-name}} memory records where possible, make sure to maintain the "label" and "detail" keys.  Only combine them if they are close enough to combine, respecting the instructions above, otherwise keep them separate.  Group similar memories to each other, they don\'t all need to be combined into one.  Return results in JSON format and respect these value types (return details as a string, not an object, etc.): {{format}}',
            antiHallucination:
                'IMPORTANT: DO NOT INCLUDE ANY OF THE ABOVE INFORMATION IN THE GENERATED RESPONSE AND ALSO DO NOT MAKE UP OR INFER ANY ADDITIONAL INFORMATION THAT IS NOT INCLUDED BELOW',
        },
        mergeIntervalMs: 0.5 * 1000,
        embeddings: {
            maxRetries: {
                create: 3,
                search: 3,
                merge: 3,
            },
            interval: {
                merge: 2 * 1000,
            },
        },
    },
    service: {
        addDebugTagToApiCalls: true,
        retryIntervalMs: 0.5 * 1000,
        backoffFactorMs: 0.5 * 1000,
    },
};
