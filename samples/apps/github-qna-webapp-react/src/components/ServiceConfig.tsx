// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Spinner, Tab, TabList, Title3 } from '@fluentui/react-components';
import { FC, useCallback, useEffect, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IBackendConfig, IKeyConfig } from '../model/KeyConfig';
import ModelConfig, { IResourceInput, ModelType } from './setup/ModelConfig';

interface IData {
    onConfigComplete: (backendConfig: IBackendConfig) => void;
    modelType: ModelType;
    backendConfig?: IBackendConfig;
    completionConfig?: IBackendConfig; // Required to validate key in embeddings configuration
}

const ServiceConfig: FC<IData> = ({
    onConfigComplete,
    modelType,
    backendConfig = {} as IBackendConfig,
    completionConfig,
}) => {
    const [isOpenAI, setIsOpenAI] = useState<boolean>(
        backendConfig?.backend !== undefined
            ? backendConfig.backend === 1
            : completionConfig?.backend !== undefined
            ? completionConfig.backend === 1
            : true,
    );
    const [completionOrEmbeddingConfig, setCompletionOrEmbeddingConfig] = useState<IBackendConfig>(backendConfig);
    const [isBusy, setIsBusy] = useState<boolean>(false);
    const sk = useSemanticKernel(process.env.REACT_APP_FUNCTION_URI as string);
    const [isValidModel, setIsValidModel] = useState(true);

    const [deploymentOrModelId, setDeploymentOrModelId] = useState<string>('');

    const [resourceInput, setResourceInput] = useState<IResourceInput>({
        key: '',
        endpoint:
            backendConfig?.endpoint ?? modelType === ModelType.Completion
                ? (process.env.REACT_APP_AZURE_OPEN_AI_COMPLETION_ENDPOINT as string)
                : (process.env.REACT_APP_AZURE_OPEN_AI_EMBEDDING_ENDPOINT as string),
    });

    const saveKey = async () => {
        setIsBusy(true);

        //POST a simple ask to validate the key
        const ask = { value: 'clippy', inputs: [{ key: 'style', value: 'Bill & Ted' }] };

        const serviceConfig: IKeyConfig = {
            completionConfig: modelType === ModelType.Completion ? completionOrEmbeddingConfig : completionConfig,
            embeddingConfig: modelType === ModelType.Embeddings ? completionOrEmbeddingConfig : undefined,
        };

        try {
            var result = await sk.invokeAsync(serviceConfig, ask, 'funskill', 'joke');
            console.log(result);
            onConfigComplete(completionOrEmbeddingConfig);
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }

        setIsBusy(false);
    };

    const setDefaults = useCallback((isOpenAi: boolean) => {
        const defaultKey: string = isOpenAi
            ? // OpenAI
              modelType === ModelType.Completion
                ? (process.env.REACT_APP_OPEN_AI_COMPLETION_KEY as string)
                : (process.env.REACT_APP_OPEN_AI_EMBEDDING_KEY as string)
            : // Azure OpenAI
            modelType === ModelType.Completion
            ? (process.env.REACT_APP_AZURE_OPEN_AI_COMPLETION_KEY as string)
            : (process.env.REACT_APP_AZURE_OPEN_AI_EMBEDDING_KEY as string);

        const defaultId: string = isOpenAi
            ? // OpenAI
              modelType === ModelType.Completion
                ? (process.env.REACT_APP_OPEN_AI_COMPLETION_MODEL as string)
                : (process.env.REACT_APP_OPEN_AI_EMBEDDING_MODEL as string)
            : // Azure OpenAI
            modelType === ModelType.Completion
            ? (process.env.REACT_APP_AZURE_OPEN_AI_COMPLETION_DEPLOYMENT as string)
            : (process.env.REACT_APP_AZURE_OPEN_AI_EMBEDDING_DEPLOYMENT as string);

        const defaultEndpoint: string = isOpenAi
            ? // OpenAI
              ''
            : // Azure OpenAI
            modelType === ModelType.Completion
            ? (process.env.REACT_APP_AZURE_OPEN_AI_COMPLETION_ENDPOINT as string)
            : (process.env.REACT_APP_AZURE_OPEN_AI_EMBEDDING_ENDPOINT as string);

        if ((backendConfig?.backend === 1 && isOpenAi) || (backendConfig?.backend === 0 && !isOpenAi)) {
            setResourceInput({ ...resourceInput, key: backendConfig.key, endpoint: backendConfig.endpoint });
            setDeploymentOrModelId(backendConfig.deploymentOrModelId);
        } else {
            setResourceInput({ ...resourceInput, key: defaultKey ?? '', endpoint: defaultEndpoint });
            setDeploymentOrModelId(defaultId ?? '');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        setDefaults(isOpenAI);
    }, [setDefaults, isOpenAI]);

    useEffect(() => {
        setCompletionOrEmbeddingConfig({
            backend: isOpenAI ? 1 : 0,
            endpoint: isOpenAI ? '' : resourceInput.endpoint,
            key: resourceInput.key,
            deploymentOrModelId: deploymentOrModelId,
            label: deploymentOrModelId,
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [resourceInput, deploymentOrModelId]);

    return (
        <>
            <Title3>Enter in your OpenAI or Azure OpenAI Service Key</Title3>
            <Body1>
                Start by entering in your OpenAI key, either from{' '}
                <a href="https://beta.openai.com/account/api-keys" target="_blank" rel="noreferrer">
                    OpenAI
                </a>{' '}
                or{' '}
                <a href="https://oai.azure.com/portal" target="_blank" rel="noreferrer">
                    Azure OpenAI Service
                </a>
            </Body1>

            <TabList
                defaultSelectedValue={isOpenAI ? 'oai' : 'aoai'}
                onTabSelect={(t, v) => {
                    setIsOpenAI(v.value === 'oai');
                }}
            >
                <Tab value="oai">OpenAI</Tab>
                <Tab value="aoai">Azure OpenAI</Tab>
            </TabList>

            {isOpenAI ? (
                <>
                    <Label htmlFor="openaikey">OpenAI Key</Label>
                    <Input
                        id="openaikey"
                        type="password"
                        value={resourceInput.key}
                        onChange={(_e, d) => {
                            setResourceInput({ ...resourceInput, key: d.value });
                            setCompletionOrEmbeddingConfig({
                                ...completionOrEmbeddingConfig,
                                key: d.value,
                            });
                        }}
                        placeholder="Enter your OpenAI key here"
                    />
                    <ModelConfig
                        isOpenAI={true}
                        modelType={modelType}
                        backendConfig={completionOrEmbeddingConfig}
                        setBackendConfig={setCompletionOrEmbeddingConfig}
                        setIsValidModel={setIsValidModel}
                        setModel={setDeploymentOrModelId}
                        resourceInput={resourceInput}
                        defaultModel={deploymentOrModelId}
                    />
                </>
            ) : (
                <>
                    <Label htmlFor="azureopenaikey">Azure OpenAI Key</Label>
                    <Input
                        id="azureopenaikey"
                        type="password"
                        value={resourceInput.key}
                        onChange={(_e, d) => {
                            setResourceInput({ ...resourceInput, key: d.value });
                            setCompletionOrEmbeddingConfig({
                                ...completionOrEmbeddingConfig,
                                key: d.value,
                            });
                        }}
                        placeholder="Enter your Azure OpenAI key here"
                    />
                    <Label htmlFor="aoaiendpoint">Endpoint</Label>
                    <Input
                        id="aoaiendpoint"
                        value={resourceInput.endpoint}
                        onChange={(e, d) => {
                            setResourceInput({ ...resourceInput, endpoint: d.value });
                            setCompletionOrEmbeddingConfig({
                                ...completionOrEmbeddingConfig,
                                endpoint: d.value,
                            });
                        }}
                        placeholder="Enter the endpoint here, ie: https://my-resource.openai.azure.com"
                    />
                    <ModelConfig
                        isOpenAI={false}
                        modelType={modelType}
                        backendConfig={completionOrEmbeddingConfig}
                        setBackendConfig={setCompletionOrEmbeddingConfig}
                        setIsValidModel={setIsValidModel}
                        setModel={setDeploymentOrModelId}
                        resourceInput={resourceInput}
                        defaultModel={deploymentOrModelId}
                    />
                </>
            )}

            <Button
                style={{ width: 70, height: 32, marginTop: 10 }}
                disabled={isBusy || !isValidModel}
                appearance="primary"
                onClick={saveKey}
            >
                Save
            </Button>
            {isBusy ? <Spinner /> : null}
        </>
    );
};

export default ServiceConfig;
