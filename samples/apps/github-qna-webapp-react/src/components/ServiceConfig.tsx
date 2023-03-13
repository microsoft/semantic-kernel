// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Spinner, Tab, TabList, Title3 } from '@fluentui/react-components';
import { FC, useEffect, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';

interface IData {
    uri: string;
    onConfigComplete: (keyConfig: IKeyConfig) => void;
}

const ServiceConfig: FC<IData> = ({ uri, onConfigComplete }) => {
    const [isOpenAI, setIsOpenAI] = useState<boolean>(true);
    const [keyConfig, setKeyConfig] = useState<IKeyConfig>({} as IKeyConfig);
    const [isBusy, setIsBusy] = useState<boolean>(false);
    const sk = useSemanticKernel(process.env.REACT_APP_FUNCTION_URI as string);

    const [openAiKey, setOpenAiKey] = useState<string>(process.env.REACT_APP_OPEN_AI_KEY as string);
    const [openAiCompletionModel, setOpenAiCompletionModel] = useState<string>(process.env.REACT_APP_OPEN_AI_COMPLETION_MODEL as string);
    const [openAiEmbeddingsModel, setOpenAiEmbeddingsModel] = useState<string>(process.env.REACT_APP_OPEN_AI_EMBEDDINGS_MODEL as string);

    const [azureOpenAiKey, setAzureOpenAiKey] = useState<string>(process.env.REACT_APP_AZURE_OPEN_AI_KEY as string);
    const [azureOpenAiCompletionDeployment, setAzureOpenAiCompletionDeployment] = useState<string>(process.env.REACT_APP_AZURE_OPEN_AI_COMPLETION_DEPLOYMENT as string);
    const [azureOpenAiEmbeddingDeployment, setAzureOpenAiEmbeddingDeployment] = useState<string>(process.env.REACT_APP_AZURE_OPEN_AI_EMBEDDING_DEPLOYMENT as string);
    const [azureOpenAiEndpoint, setAzureOpenAiEndpoint] = useState<string>(process.env.REACT_APP_AZURE_OPEN_AI_ENDPOINT as string);

    const saveKey = async () => {
        setIsBusy(true);

        //POST a simple ask to validate the key
        const ask = { value: 'clippy', inputs: [{ key: 'style', value: 'Bill & Ted' }] };

        try {
            var result = await sk.invokeAsync(keyConfig, ask, 'funskill', 'joke');
            console.log(result);
            onConfigComplete(keyConfig);
        }
        catch {
            alert('Something went wrong, please check you have the function running and that it is accessible by the web app');
        }

        setIsBusy(false);
    }

    useEffect(() => {
        setKeyConfig(keyConfig => ({
            ...keyConfig,
            key: isOpenAI ? openAiKey : azureOpenAiKey,
            completionDeploymentOrModelId: isOpenAI ? openAiCompletionModel : azureOpenAiCompletionDeployment,
            embeddingDeploymentOrModelId: isOpenAI ? openAiEmbeddingsModel : azureOpenAiEmbeddingDeployment,
            endpoint: isOpenAI ? '' : azureOpenAiEndpoint,
            completionBackend: isOpenAI ? 1 : 0,
            embeddingBackend: isOpenAI ? 1 : 0
        }));
    }, [isOpenAI, openAiKey, openAiCompletionModel, openAiEmbeddingsModel, azureOpenAiKey, azureOpenAiCompletionDeployment, azureOpenAiEmbeddingDeployment, azureOpenAiEndpoint]);

    return (
        <>
            <Title3>Enter in your OpenAI or Azure OpenAI Service Key</Title3>
            <Body1>Start by entering in your OpenAI key, either from <a href='https://beta.openai.com/account/api-keys' target='_blank' rel="noreferrer">OpenAI</a> or <a href='https://oai.azure.com/portal' target='_blank' rel="noreferrer">Azure OpenAI Service</a></Body1>

            <TabList defaultSelectedValue="oai" onTabSelect={(t, v) => setIsOpenAI(v.value === 'oai')}>
                <Tab value="oai">OpenAI</Tab>
                <Tab value="aoai">Azure OpenAI</Tab>
            </TabList>

            {
                isOpenAI ?
                    <>
                        <Label htmlFor='openaikey'>OpenAI Key</Label>
                        <Input id='openaikey' type='password' value={openAiKey} onChange={(e, d) => { setOpenAiKey(d.value); setKeyConfig({ ...keyConfig, key: d.value }) }} placeholder='Enter your OpenAI key here' />
                        <Label htmlFor='oaicompletionmodel'>Completion Model</Label>
                        <Input id='oaicompletionmodel' value={openAiCompletionModel} onChange={(e, d) => { setOpenAiCompletionModel(d.value); setKeyConfig({ ...keyConfig, completionDeploymentOrModelId: d.value, label: d.value }) }} placeholder='Enter the model id here, ie: text-davinci-003' />
                        <Label htmlFor='oaiembeddingsmodel'>Embeddings Model</Label>
                        <Input id='oaiembeddingsmodel' value={openAiEmbeddingsModel} onChange={(e, d) => { setOpenAiEmbeddingsModel(d.value); setKeyConfig({ ...keyConfig, embeddingDeploymentOrModelId: d.value, label: d.value }) }} placeholder='Enter the embeddings model id here, ie: text-embedding-ada-002' />
                    </> :
                    <>
                        <Label htmlFor='azureopenaikey'>Azure OpenAI Key</Label>
                        <Input id='azureopenaikey' type='password' value={azureOpenAiKey} onChange={(e, d) => { setAzureOpenAiKey(d.value); setKeyConfig({ ...keyConfig, key: d.value }) }} placeholder='Enter your Azure OpenAI key here' />
                        <Label htmlFor='aoaicompletionmodel'>Completion Model</Label>
                        <Input id='aoaicompletiondeployment' value={azureOpenAiCompletionDeployment} onChange={(e, d) => { setAzureOpenAiCompletionDeployment(d.value); setKeyConfig({ ...keyConfig, completionDeploymentOrModelId: d.value, label: d.value }) }} placeholder='Enter your deployment id here, ie: my-deployment' />
                        <Label htmlFor='aoaiembeddingmodel'>Embedding Model</Label>
                        <Input id='aoaiebeddingdeployment' value={azureOpenAiEmbeddingDeployment} onChange={(e, d) => { setAzureOpenAiEmbeddingDeployment(d.value); setKeyConfig({ ...keyConfig, embeddingDeploymentOrModelId: d.value, label: d.value }) }} placeholder='Enter your deployment id here, ie: my-deployment' />
                        <Label htmlFor='aoaiendpoint'>Endpoint</Label>
                        <Input id='aoaiendpoint' value={azureOpenAiEndpoint} onChange={(e, d) => { setAzureOpenAiEndpoint(d.value); setKeyConfig({ ...keyConfig, endpoint: d.value }) }} placeholder='Enter the endpoint here, ie: https://my-resource.openai.azure.com' />
                    </>
            }

            <Button style={{ width: 70, height: 32 }} disabled={isBusy} appearance="primary" onClick={saveKey}>Save</Button>
            {isBusy ? <Spinner /> : null}
        </>
    )
}

export default ServiceConfig;