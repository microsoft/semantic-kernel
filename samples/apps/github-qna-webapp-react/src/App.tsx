// Copyright (c) Microsoft. All rights reserved.

import { Subtitle1, Tab, TabList } from '@fluentui/react-components';
import { FC, useEffect, useState } from 'react';
import FunctionProbe from './components/FunctionProbe';
import GitHubProjectSelection from './components/GitHubRepoSelection';
import QnA from './components/QnA';
import QuickTips, { ITipGroup } from './components/QuickTips';
import ServiceConfig from './components/ServiceConfig';
import { ModelType } from './components/setup/ModelConfig';
import { IKeyConfig } from './model/KeyConfig';

const App: FC = () => {
    enum AppState {
        ProbeForFunction = 0,
        Setup = 1,
        ConfigureCompletionModel = 2,
        ConfigureEmbeddingModel = 3,
        GitHubProject = 4,
        QnA = 5,
    }

    const appStateToTabValueMap = new Map<AppState, string>([
        [AppState.Setup, 'setup'],
        [AppState.ConfigureCompletionModel, 'completion'],
        [AppState.ConfigureEmbeddingModel, 'embedding'],
        [AppState.GitHubProject, 'github'],
        [AppState.QnA, 'qna'],
    ]);
    const tabValueToAppStateMap = new Map<string, AppState>([
        ['setup', AppState.ConfigureCompletionModel],
        ['completion', AppState.ConfigureCompletionModel],
        ['embedding', AppState.ConfigureEmbeddingModel],
        ['github', AppState.GitHubProject],
        ['qna', AppState.QnA],
    ]);

    const [keyConfig, setKeyConfig] = useState<IKeyConfig>();
    const [appState, setAppState] = useState<AppState>(AppState.ProbeForFunction);
    const [selectedTabValue, setSelectedTabValue] = useState<string>('completion');
    const [project, setProject] = useState<string>('');
    const [branch, setBranch] = useState<string>('');

    useEffect(() => {
        changeAppState(appState);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [appState]);

    const changeAppState = function (newAppState: AppState) {
        setAppState(newAppState);
        setSelectedTabValue(appStateToTabValueMap.get(newAppState) ?? 'completion');
    };
    const changeTabValue = function (newTabValue: string) {
        setSelectedTabValue(newTabValue);
        setAppState(tabValueToAppStateMap.get(newTabValue) ?? AppState.Setup);
    };

    const tips: ITipGroup[] = [
        {
            header: 'Useful Resources',
            items: [
                {
                    title: 'Read Documentation',
                    uri: 'https://aka.ms/sk/github-bot',
                },
            ],
        },
        {
            header: 'Functions used in this sample',
            items: [
                {
                    title: 'Q&A',
                    uri: 'https://aka.ms/sk/repo/githubbot/QA',
                },
                {
                    title: 'Pull Web Content',
                    uri: 'https://aka.ms/sk/repo/githubbot/pullwebcontent',
                },
            ],
        },
        {
            header: 'Learn more about',
            items: [
                {
                    title: 'Memories',
                    uri: 'https://aka.ms/sk/memories',
                },
                {
                    title: 'Embeddings',
                    uri: 'https://aka.ms/sk/embeddings',
                },
            ],
        },
        {
            header: 'Local SK URL',
            items: [
                {
                    title: process.env.REACT_APP_FUNCTION_URI as string,
                    uri: process.env.REACT_APP_FUNCTION_URI as string,
                },
            ],
        },
    ];

    return (
        <div id="container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            <div id="header">
                <Subtitle1 as="h1">GitHub Repo Q&A Bot</Subtitle1>
            </div>

            {appState === AppState.ProbeForFunction ? (
                <FunctionProbe
                    uri={process.env.REACT_APP_FUNCTION_URI as string}
                    onFunctionFound={() => setAppState(AppState.ConfigureCompletionModel)}
                />
            ) : null}

            <div
                style={{
                    display: 'flex',
                    flexDirection: 'row',
                    gap: 10,
                    flex: 1,
                    height: '90vh',
                    alignContent: 'start',
                    justifyContent: 'space-between',
                }}
            >
                <div id="content">
                    {appState === AppState.ProbeForFunction ? null : (
                        <TabList
                            style={{ paddingTop: 60, paddingLeft: 20 }}
                            selectedValue={selectedTabValue}
                            vertical
                            size="large"
                            onTabSelect={(_, data) => {
                                if (data.value === 'setup') data.value = 'completion';
                                changeTabValue(data.value as string);
                            }}
                        >
                            <Tab value="setup">Setup</Tab>
                            <Tab value="completion" style={{ marginLeft: 10, paddingRight: 0 }}>
                                Completion Model
                            </Tab>
                            <Tab
                                value="embedding"
                                style={{ marginLeft: 10, paddingRight: 0 }}
                                disabled={!keyConfig?.completionConfig}
                            >
                                Embedding Model
                            </Tab>
                            <Tab value="github" disabled={appState < AppState.GitHubProject}>
                                GitHub Repository
                            </Tab>
                            <Tab value="qna" disabled={appState < AppState.QnA}>
                                Q&A
                            </Tab>
                        </TabList>
                    )}
                    <div id="main">
                        {appState === AppState.ConfigureCompletionModel ? (
                            <ServiceConfig
                                onConfigComplete={(backendConfig) => {
                                    setKeyConfig({
                                        ...keyConfig,
                                        embeddingConfig: keyConfig?.embeddingConfig,
                                        completionConfig: backendConfig,
                                    });
                                    setAppState(AppState.ConfigureEmbeddingModel);
                                }}
                                modelType={ModelType.Completion}
                                backendConfig={keyConfig?.completionConfig}
                            />
                        ) : null}
                        {appState === AppState.ConfigureEmbeddingModel ? (
                            <ServiceConfig
                                onConfigComplete={(backendConfig) => {
                                    setKeyConfig({
                                        ...keyConfig,
                                        completionConfig: keyConfig?.completionConfig,
                                        embeddingConfig: backendConfig,
                                    });
                                    setAppState(AppState.GitHubProject);
                                }}
                                modelType={ModelType.Embeddings}
                                backendConfig={keyConfig?.embeddingConfig}
                                completionConfig={keyConfig?.completionConfig}
                            />
                        ) : null}
                        {appState === AppState.GitHubProject ? (
                            <GitHubProjectSelection
                                keyConfig={keyConfig!}
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                prevProject={project}
                                prevBranch={branch}
                                onLoadProject={(project, branch) => {
                                    setProject(project);
                                    setBranch(branch);
                                    setAppState(AppState.QnA);
                                }}
                                onBack={() => {
                                    changeAppState(appState - 1);
                                }}
                            />
                        ) : null}

                        {appState === AppState.QnA && project !== undefined && branch !== undefined ? (
                            <QnA
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                keyConfig={keyConfig!}
                                project={project}
                                branch={branch}
                                onBack={() => {
                                    changeAppState(appState - 1);
                                }}
                            />
                        ) : null}
                    </div>
                </div>
                {appState === AppState.ProbeForFunction ? null : (
                    <div id="tipbar">
                        <QuickTips tips={tips} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default App;
