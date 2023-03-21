// Copyright (c) Microsoft. All rights reserved.

import { Dropdown, Label, Link, Option, OptionGroup, Spinner } from '@fluentui/react-components';
import { InfoLabel } from '@fluentui/react-components/unstable';
import { FC, useEffect, useState } from 'react';
import '../../App.css';
import { IBackendConfig } from '../../model/KeyConfig';

interface IData {
    isOpenAI: boolean;
    modelType: ModelType;
    backendConfig: IBackendConfig;
    setBackendConfig: React.Dispatch<React.SetStateAction<IBackendConfig>>;
    keyConfig: {
        key: string;
        endpoint: string;
    };
    setModel: (value: React.SetStateAction<string>) => void;
    defaultModel?: string;
}

export enum ModelType {
    Embeddings,
    Completion,
}

interface ModelOption {
    id: string;
    disabled: boolean;
}

type AzureOpenAIModels = {
    otherModels: ModelOption[];
    completionModels: ModelOption[];
    embeddingsModels: ModelOption[];
};

type OpenAIModels = {
    otherModels: ModelOption[];
    probableEmbeddingsModels: ModelOption[];
};

const ModelConfig: FC<IData> = ({ isOpenAI, modelType, setModel, backendConfig, keyConfig, defaultModel = '' }) => {
    const modelTitle = modelType === ModelType.Embeddings ? ['embeddings', 'Embeddings'] : ['completion', 'Completion'];
    const labelPrefix = `${isOpenAI ? 'oai' : 'aoai'}${modelTitle[0]}`;
    const [suggestedModels, setSuggestedModels] = useState<ModelOption[] | undefined>();
    const [modelIds, setModelIds] = useState<ModelOption[] | undefined>();
    const [isBusy, setIsBusy] = useState(false);
    const [selectedModel, setSelectedModel] = useState(defaultModel);

    useEffect(() => {
        setSelectedModel(defaultModel);
        if (keyConfig && ((backendConfig?.backend === 1 && isOpenAI) || (backendConfig?.backend === 0 && !isOpenAI))) {
            const onFailure = (errorMessage?: string) => {
                alert(errorMessage);
                setIsBusy(false);
                setSelectedModel('');
                return undefined;
            };

            const fetchModels = keyConfig.key && ((!isOpenAI && keyConfig.endpoint) || isOpenAI);

            const setModels = (backendModels?: AzureOpenAIModels | OpenAIModels) => {
                const completionModels = isOpenAI
                    ? backendModels?.otherModels
                    : (backendModels as AzureOpenAIModels).completionModels;
                const embeddingsModels = isOpenAI
                    ? (backendModels as OpenAIModels).probableEmbeddingsModels
                    : (backendModels as AzureOpenAIModels).embeddingsModels;

                const sortedCompletionModelsArray = completionModels?.sort((a, b) => a.id.localeCompare(b.id));
                const sortedEmbeddingsModelArray = embeddingsModels?.sort((a, b) => a.id.localeCompare(b.id));
                if (modelType == ModelType.Embeddings) {
                    setModelIds(sortedCompletionModelsArray);
                    setSuggestedModels(sortedEmbeddingsModelArray);
                } else {
                    setSuggestedModels(sortedCompletionModelsArray);
                    setModelIds(sortedEmbeddingsModelArray);
                }
                setIsBusy(false);
            };

            if (fetchModels) {
                setIsBusy(true);
                if (isOpenAI) {
                    getOpenAiModels(keyConfig.key, onFailure).then((value) => setModels(value));
                } else {
                    getAzureOpenAiDeployments(keyConfig.key, keyConfig.endpoint, onFailure).then((value) =>
                        setModels(value),
                    );
                }
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [keyConfig]);

    return (
        <div style={{ paddingTop: 20, gap: 10, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            {isOpenAI ? (
                <InfoLabel
                    info={
                        <div style={{ maxWidth: 250 }}>
                            Please note this drop down lists all available models but not all models will work as{' '}
                            {(modelType === ModelType.Completion ? 'a ' : 'an ') + modelTitle[0]} model. We've suggested
                            some based on common naming patterns for these models.{' '}
                            <Link href="https://platform.openai.com/docs/models">Learn more</Link>{' '}
                        </div>
                    }
                    htmlFor={`${labelPrefix}model`}
                >
                    {modelTitle[1]} Model
                </InfoLabel>
            ) : (
                <Label htmlFor={`${labelPrefix}model`}> {modelTitle[1]} Model</Label>
            )}
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
                    onOptionSelect={(_e, model) => {
                        setSelectedModel(model.optionValue ?? '');
                        setModel(model.optionValue ?? '');
                    }}
                >
                    {suggestedModels ? (
                        <OptionGroup label={`${isOpenAI ? 'Suggested ' : ''}${modelTitle[1]} Models`}>
                            {suggestedModels.map((option) => (
                                <Option key={option.id} disabled={option.disabled}>
                                    {option.id}
                                </Option>
                            ))}
                        </OptionGroup>
                    ) : null}
                    {modelIds ? (
                        <OptionGroup label={suggestedModels ? 'Other' : 'All models'}>
                            {modelIds.map((option) => (
                                <Option key={option.id} disabled={option.disabled}>
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
    const modelsRequestUrl = aoaiEndpoint + modelsPath;

    let init: RequestInit = {
        method: 'GET',
        headers: {
            'api-key': apiKey,
        },
    };

    return fetch(modelsRequestUrl, init)
        .then(async (response) => {
            if (!response || !response.ok) {
                throw new Error(await response?.clone().text());
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
                    completionModels: [] as ModelOption[],
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
                        ids.completionModels.push({
                            id: deployment.id,
                            disabled: deployment.status && deployment.status !== 'succeeded',
                        });
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
            return onFailureCallback(e);
        });
};

/* OpenAI Get Models API response does not have any property differentiating model types
 * so we have make inferences based on common naming patterns,
 * where embedding models usually contain "embedding" or "search"
 * See more: https://platform.openai.com/docs/models/model-endpoint-compatibility
 */
const getOpenAiModels = async (apiKey: string, onFailureCallback: (errorMessage?: string) => undefined) => {
    const requestUrl = 'https://api.openai.com/v1/models';

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
        return onFailureCallback(await response?.clone().text());
    }

    const models = await response!
        .clone()
        .json()
        .then((body) => {
            return body.data;
        });

    const ids = {
        probableEmbeddingsModels: [] as ModelOption[],
        otherModels: [] as ModelOption[],
    };
    for (const key in models) {
        const model = models[key];
        if (model.id.includes('embedding') || model.id.includes('search')) {
            ids.probableEmbeddingsModels.push({
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
