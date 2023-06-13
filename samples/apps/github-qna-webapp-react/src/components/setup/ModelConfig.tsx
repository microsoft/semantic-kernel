// Copyright (c) Microsoft. All rights reserved.

import { Dropdown, Link, Option, OptionGroup, Spinner, Text } from '@fluentui/react-components';
import { InfoLabel } from '@fluentui/react-components/unstable';
import { FC, useEffect, useState } from 'react';
import '../../App.css';
import { IBackendConfig } from '../../model/KeyConfig';

interface IData {
    isOpenAI: boolean;
    modelType: ModelType;
    backendConfig: IBackendConfig;
    setBackendConfig: React.Dispatch<React.SetStateAction<IBackendConfig>>;
    resourceInput: IResourceInput;
    setIsValidModel: (value: React.SetStateAction<boolean>) => void;
    setModel: (value: React.SetStateAction<string>) => void;
    defaultModel?: string;
}

export enum ModelType {
    Embeddings = 'embedding',
    Completion = 'completion',
}

interface ModelOption {
    id: string;
    disabled: boolean;
}

export type IResourceInput = Pick<IBackendConfig, 'key' | 'endpoint'>;

type AIModels = {
    otherModels: ModelOption[];
    chatCompletionModels: ModelOption[];
    textCompletionModels?: ModelOption[];
    embeddingsModels: ModelOption[];
};

const GenericFetchErrorMessage = 'Failed to fetch';

const ModelConfig: FC<IData> = ({
    isOpenAI,
    modelType,
    setModel,
    backendConfig,
    resourceInput,
    setIsValidModel,
    defaultModel = '',
}) => {
    const modelTitle =
        modelType === ModelType.Embeddings ? ['embeddings', 'Embeddings'] : ['chat completion', 'Chat Completion'];
    const labelPrefix = `${isOpenAI ? 'oai' : 'aoai'}${modelTitle[0]}`;
    const [suggestedModels, setSuggestedModels] = useState<ModelOption[] | undefined>();
    const [modelIds, setModelIds] = useState<ModelOption[] | undefined>();
    const [isBusy, setIsBusy] = useState(false);
    const [selectedModel, setSelectedModel] = useState(defaultModel);
    const [errorMessage, setErrorMessage] = useState<string | undefined>();

    useEffect(() => {
        setSelectedModel(defaultModel);
        setIsValidModel(true);
        if (
            resourceInput &&
            ((backendConfig?.backend === 1 && isOpenAI) || (backendConfig?.backend === 0 && !isOpenAI))
        ) {
            const onFailure = (error?: string) => {
                if (error?.includes(GenericFetchErrorMessage))
                    error += `. Check that you've entered your key ${isOpenAI ? '' : 'and endpoint '}correctly.`;
                setSuggestedModels(undefined);
                setModelIds(undefined);
                setErrorMessage(error);
                setIsBusy(false);
                setSelectedModel('');
                return undefined;
            };

            const fetchModels = resourceInput.key && ((!isOpenAI && resourceInput.endpoint) || isOpenAI);

            const setModels = (backendModels?: AIModels) => {
                const chatCompletionModels = backendModels?.chatCompletionModels ?? [];
                const embeddingsModels = backendModels?.embeddingsModels ?? [];
                var otherModels = (isOpenAI ? backendModels?.otherModels : backendModels?.textCompletionModels) ?? [];

                if (modelType === ModelType.Embeddings) {
                    setSuggestedModels(embeddingsModels.sort((a, b) => a.id.localeCompare(b.id)));
                    setModelIds(otherModels.concat(chatCompletionModels).sort((a, b) => a.id.localeCompare(b.id)));
                } else {
                    setSuggestedModels(chatCompletionModels.sort((a, b) => a.id.localeCompare(b.id)));
                    setModelIds(otherModels.concat(embeddingsModels).sort((a, b) => a.id.localeCompare(b.id)));
                }
                setIsBusy(false);
            };

            if (fetchModels) {
                setIsBusy(true);
                setErrorMessage(undefined);
                if (isOpenAI) {
                    getOpenAiModels(resourceInput.key, onFailure).then((value) => {
                        if (value) setModels(value);
                    });
                } else {
                    getAzureOpenAiDeployments(resourceInput.key, resourceInput.endpoint, onFailure).then((value) => {
                        if (value) setModels(value);
                    });
                }
            } else {
                setSuggestedModels(undefined);
                setModelIds(undefined);
                setSelectedModel('');
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [resourceInput, backendConfig.backend]);

    const onOptionSelect = (_e: any, model: { optionValue?: string }) => {
        setSelectedModel(model.optionValue ?? '');

        // We only need to validate Open AI models since we've already filtered for valid
        // Azure Open AI models using the capabilities property when setting the Dropdown options
        if (isOpenAI) {
            setIsBusy(true);
            setIsValidModel(false);
            setErrorMessage(undefined);

            isValidOpenAIConfig(resourceInput, model.optionValue ?? '', modelType)
                .then((response) => {
                    setIsValidModel(response);
                    if (response) {
                        setModel(model.optionValue ?? '');
                    }
                })
                .catch((e) => {
                    setErrorMessage(e.message ?? `Something went wrong.\n\nDetails:\n' + ${e}`);
                })
                .finally(() => {
                    setIsBusy(false);
                });
        } else {
            setIsValidModel(true);
            setModel(model.optionValue ?? '');
        }
    };

    return (
        <div style={{ paddingTop: 20, gap: 10, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <InfoLabel
                info={
                    isOpenAI ? (
                        <div style={{ maxWidth: 275 }}>
                            This drop down lists all available models, but not all models support {modelTitle[0]}. We've
                            suggested some based on common naming patterns for these models.{' '}
                            <Link href="https://platform.openai.com/docs/models">Learn more</Link>{' '}
                        </div>
                    ) : (
                        <div style={{ maxWidth: 275 }}>
                            This drop down lists all deployments owned by the Azure OpenAI resource, but not all models
                            support {modelTitle[0]}. We've disabled the models that don't have "{modelTitle[0]}"
                            capability.{' '}
                            <Link href="https://learn.microsoft.com/en-us/rest/api/cognitiveservices/azureopenaistable/models/list?tabs=HTTP#capabilities">
                                Learn more
                            </Link>{' '}
                        </div>
                    )
                }
                htmlFor={`${labelPrefix}model`}
            >
                {modelTitle[1]} Model
            </InfoLabel>
            {!!errorMessage ? <Text style={{ color: 'rgb(163, 21, 21)' }}> {`${errorMessage}`}</Text> : null}
            <div style={{ display: 'flex', gap: 10, flexDirection: 'row', alignItems: 'left' }}>
                {isBusy ? <Spinner size="tiny" /> : null}
                <Dropdown
                    aria-labelledby={`${labelPrefix}model`}
                    value={selectedModel}
                    placeholder={
                        modelIds
                            ? 'Select a model id'
                            : `Enter valid key ${isOpenAI ? '' : 'and endpoint'} to load models`
                    }
                    onOptionSelect={onOptionSelect}
                >
                    {suggestedModels ? (
                        <OptionGroup label={`${isOpenAI ? 'Suggested ' : ''}${modelTitle[1]} Models`}>
                            {suggestedModels.map((option, index) => (
                                <Option key={index} disabled={option.disabled} text={option.id}>
                                    {option.id}
                                </Option>
                            ))}
                        </OptionGroup>
                    ) : null}
                    {modelIds ? (
                        <OptionGroup label={suggestedModels ? 'Other' : 'All models'}>
                            {modelIds.map((option) => (
                                <Option key={option.id} disabled={!isOpenAI || option.disabled}>
                                    {option.id}
                                </Option>
                            ))}
                        </OptionGroup>
                    ) : null}
                </Dropdown>
            </div>
        </div>
    );
};

export default ModelConfig;

/* Azure OpenAI Get Models API response includes capabilities as a property,
 * allowing us to differentiate between model types
 * See more: https://learn.microsoft.com/en-us/rest/api/cognitiveservices/azureopenaistable/models/list?tabs=HTTP#capabilities
 */
const getAzureOpenAiDeployments = async (
    apiKey: string,
    aoaiEndpoint: string,
    onFailureCallback: (errorMessage?: string) => undefined,
) => {
    const currentAoaiApiVersion = '2022-12-01';

    const aoaiCompletionModels = new Set();
    const aoaiEmbeddingsModels = new Set();

    const modelsPath = `/openai/models?api-version=${currentAoaiApiVersion}`;
    let modelsRequestUrl: URL;
    try {
        modelsRequestUrl = new URL(modelsPath, aoaiEndpoint);
    } catch (_e) {
        return onFailureCallback(GenericFetchErrorMessage);
    }

    let init: RequestInit = {
        method: 'GET',
        headers: {
            'api-key': apiKey,
        },
    };

    return fetch(modelsRequestUrl, init)
        .then(async (response) => {
            if (!response || !response.ok) {
                throw new Error(await getErrorMessage(response));
            }

            const models = await response!
                .clone()
                .json()
                .then((body) => {
                    return body.data;
                });

            for (const key in models) {
                const model = models[key];
                if (model.capabilities?.completion === true) {
                    aoaiCompletionModels.add(model.id);
                } else if (model.capabilities?.embeddings === true) {
                    aoaiEmbeddingsModels.add(model.id);
                }
            }

            const deploymentsPath = `/openai/deployments?api-version=${currentAoaiApiVersion}`;
            const deploymentsRequestUrl = aoaiEndpoint + deploymentsPath;

            return await fetch(deploymentsRequestUrl, init).then(async (response) => {
                const deployments = await response!
                    .clone()
                    .json()
                    .then((body) => {
                        return body.data;
                    });

                const ids = {
                    embeddingsModels: [] as ModelOption[],
                    textCompletionModels: [] as ModelOption[],
                    chatCompletionModels: [] as ModelOption[],
                    otherModels: [] as ModelOption[],
                };
                for (const key in deployments) {
                    const deployment = deployments[key];
                    if (aoaiEmbeddingsModels.has(deployment.model)) {
                        ids.embeddingsModels.push({
                            id: deployment.id,
                            disabled: deployment.status && deployment.status !== 'succeeded',
                        });
                    } else if (aoaiCompletionModels.has(deployment.model)) {
                        if (deployment.model.includes('gpt')) {
                            ids.chatCompletionModels.push({
                                id: deployment.id,
                                disabled: deployment.status && deployment.status !== 'succeeded',
                            });
                        } else {
                            ids.textCompletionModels.push({
                                id: deployment.id,
                                disabled: deployment.status && deployment.status !== 'succeeded',
                            });
                        }
                    } else {
                        ids.otherModels.push({
                            id: deployment.id,
                            disabled: deployment.status && deployment.status !== 'succeeded',
                        });
                    }
                }
                return ids;
            });
        })
        .catch((e) => {
            return onFailureCallback(e.message ?? GenericFetchErrorMessage);
        });
};

/* OpenAI Get Models API response does not have any property differentiating model types
 * so we have make inferences based on common naming patterns,
 * where embedding models usually contain "embedding" or "search"
 * See more: https://platform.openai.com/docs/models/model-endpoint-compatibility
 */
const getOpenAiModels = async (apiKey: string, onFailureCallback: (errorMessage?: string) => undefined) => {
    const requestUrl = new URL('https://api.openai.com/v1/models');

    let init: RequestInit = {
        method: 'GET',
        headers: { Authorization: `Bearer ${apiKey}` },
    };

    let response: Response | undefined = undefined;
    try {
        response = await fetch(requestUrl, init);
    } catch (e) {
        return onFailureCallback(e as string);
    }
    if (!response || !response.ok) {
        return onFailureCallback(await getErrorMessage(response));
    }

    const models = await response!
        .clone()
        .json()
        .then((body) => {
            return body.data;
        });

    const ids = {
        embeddingsModels: [] as ModelOption[],
        textCompletionModels: [] as ModelOption[],
        chatCompletionModels: [] as ModelOption[],
        otherModels: [] as ModelOption[],
    };
    for (const key in models) {
        const model = models[key];
        if (model.id.includes('embedding') || model.id.includes('search')) {
            ids.embeddingsModels.push({
                id: model.id,
                disabled: model.status && model.status !== 'succeeded',
            });
        } else if (model.id.includes('gpt')) {
            ids.chatCompletionModels.push({
                id: model.id,
                disabled: model.status && model.status !== 'succeeded',
            });
        } else {
            ids.otherModels.push({
                id: model.id,
                disabled: model.status && model.status !== 'succeeded',
            });
        }
    }
    return ids;
};

const isValidOpenAIConfig = async (resourceInput: IResourceInput, model: string, modelType: ModelType) => {
    const modelObject = modelType === ModelType.Completion ? 'chat/completions' : 'embeddings';
    const inputText = 'Tell me a short joke.';
    const bodyInput =
        modelType === ModelType.Completion
            ? { messages: [{ role: 'user', content: inputText }] }
            : { input: inputText };

    return fetch('https://api.openai.com/v1/' + modelObject, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${resourceInput.key}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ...bodyInput,
            model: model,
            max_tokens: 100,
        }),
    }).then(async (response) => {
        if (!response || !response.ok) {
            let errorMessage = await getErrorMessage(response);
            if (response.status === 404 || response.status === 500) {
                errorMessage = `This is not a supported ${modelType} model`;
            }
            throw new Error(`${errorMessage}. Please select a different one.`);
        }

        return true;
    });
};

const getErrorMessage = async (response: Response) => {
    const responseMessage = `${GenericFetchErrorMessage}: ${response.status} error`;
    if (response.status >= 500 && response.status < 600) {
        return responseMessage;
    }
    const responseJson = await response?.clone().json();
    return responseJson.error?.message ?? responseMessage;
};
