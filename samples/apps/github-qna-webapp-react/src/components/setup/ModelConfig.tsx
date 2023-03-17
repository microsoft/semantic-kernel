// Copyright (c) Microsoft. All rights reserved.

import { Dropdown, Link, Option, OptionGroup, Spinner } from '@fluentui/react-components';
import { InfoLabel } from '@fluentui/react-components/unstable';
import { FC, useEffect, useState } from 'react';
import '../../App.css';
import { IBackendConfig } from '../../model/KeyConfig';

interface IData {
    isOpenAI: boolean;
    modelType: ModelType;
    backendConfig: IBackendConfig;
    setBackendConfig: React.Dispatch<React.SetStateAction<IBackendConfig>>;
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

const ModelConfig: FC<IData> = ({
    isOpenAI,
    modelType,
    setModel,
    backendConfig,
    setBackendConfig,
    defaultModel = '',
}) => {
    const modelTitle = modelType === ModelType.Embeddings ? ['embeddings', 'Embeddings'] : ['completion', 'Completion'];
    const labelPrefix = `${isOpenAI ? 'oai' : 'aoai'}${modelTitle[0]}`;
    const [suggestedModels, setSuggestedModels] = useState<ModelOption[] | undefined>();
    const [modelIds, setModelIds] = useState<ModelOption[] | undefined>();
    const [isBusy, setIsBusy] = useState(false);
    const [selectedModel, setSelectedModel] = useState(defaultModel);

    useEffect(() => {
        setSelectedModel(defaultModel);
        if (
            backendConfig &&
            ((backendConfig?.backend === 1 && isOpenAI) || (backendConfig?.backend === 0 && !isOpenAI))
        ) {
            const getModels = async (isOpenAI: boolean, apiKey: string, aoaiEndpoint?: string) => {
                setModelIds(undefined);
                const currentAoaiApiVersion = '2022-12-01';

                const baseUrl = isOpenAI ? 'https://api.openai.com/v1/' : aoaiEndpoint;
                const path = !isOpenAI ? `/openai/deployments?api-version=${currentAoaiApiVersion}` : 'models';
                const requestUrl = baseUrl + path;

                let init: RequestInit = {
                    method: 'GET',
                    headers: isOpenAI
                        ? { Authorization: `Bearer ${apiKey}` }
                        : {
                              'api-key': apiKey,
                          },
                };

                const onFailure = (errorMessage?: string) => {
                    alert(errorMessage);
                    setIsBusy(false);
                    setSelectedModel('');
                    return undefined;
                };

                let response: Response | undefined = undefined;
                try {
                    response = await fetch(requestUrl, init);
                } catch (e) {
                    return onFailure(e as string);
                }
                if (!response || !response.ok) {
                    return onFailure(await response?.clone().text());
                }

                const models = await response!
                    .clone()
                    .json()
                    .then((body) => {
                        return body.data;
                    });

                const ids = {
                    probableEmbeddingModels: [] as ModelOption[],
                    otherModels: [] as ModelOption[],
                };
                for (const key in models) {
                    const model = models[key];
                    if (model.id.includes('embedding') || model.id.includes('search')) {
                        ids.probableEmbeddingModels.push({
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

            const fetchModels = backendConfig.key && ((!isOpenAI && backendConfig.endpoint) || isOpenAI);

            if (fetchModels) {
                setIsBusy(true);
                getModels(isOpenAI, backendConfig.key, isOpenAI ? undefined : backendConfig.endpoint).then((value) => {
                    const sortedOthersArray = value?.otherModels.sort((a, b) => a.id.localeCompare(b.id));
                    const sortedEmbeddingsArray = value?.probableEmbeddingModels.sort((a, b) =>
                        a.id.localeCompare(b.id),
                    );
                    if (modelType == ModelType.Embeddings) {
                        setModelIds(sortedOthersArray);
                        setSuggestedModels(sortedEmbeddingsArray);
                    } else {
                        setSuggestedModels(sortedOthersArray);
                        setModelIds(sortedEmbeddingsArray);
                    }
                    setIsBusy(false);
                });
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [backendConfig.key, backendConfig.endpoint]);

    return (
        <div style={{ paddingTop: 20, gap: 10, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
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
                        setBackendConfig({
                            ...backendConfig,
                            deploymentOrModelId: model.optionValue ?? '',
                            label: model.optionValue ?? '',
                        });
                    }}
                >
                    {suggestedModels ? (
                        <OptionGroup label={`Suggested ${modelTitle[1]} Models`}>
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
