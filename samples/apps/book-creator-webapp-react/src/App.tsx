// Copyright (c) Microsoft. All rights reserved.

import { Subtitle1, Tab, TabList } from '@fluentui/react-components';
import { FC, useEffect, useState } from 'react';
import CreateBookWithPlanner from './components/CreateBookWithPlanner';
import FunctionProbe from './components/FunctionProbe';
import QuickTips, { ITipGroup } from './components/QuickTips';
import ServiceConfig from './components/ServiceConfig';
import TopicSelection from './components/TopicSelection';
import { IKeyConfig } from './model/KeyConfig';

const App: FC = () => {
    enum AppState {
        ProbeForFunction = 0,
        Setup = 1,
        Interact = 2,
        CreateBook = 3,
    }

    const appStateToTabValueMap = new Map<AppState, string>([
        [AppState.Setup, 'setup'],
        [AppState.Interact, 'interact'],
        [AppState.CreateBook, 'createbook'],
    ]);
    const tabValueToAppStateMap = new Map<string, AppState>([
        ['setup', AppState.Setup],
        ['interact', AppState.Interact],
        ['createbook', AppState.CreateBook],
    ]);

    const [keyConfig, setKeyConfig] = useState<IKeyConfig>();
    const [appState, setAppState] = useState<AppState>(AppState.ProbeForFunction);
    const [selectedTabValue, setSelectedTabValue] = useState<string>('setup');
    const [title, setTitle] = useState<string>();
    const [description, setDescription] = useState<string>();

    useEffect(() => {
        changeAppState(appState);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [appState]);

    const changeAppState = function (newAppState: AppState) {
        setAppState(newAppState);
        setSelectedTabValue(appStateToTabValueMap.get(newAppState) ?? 'setup');
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
                    uri: 'https://aka.ms/SKDocBook',
                },
            ],
        },
        {
            header: 'Functions used in this sample',
            items: [
                {
                    title: 'Book ideas',
                    uri: 'https://github.com/microsoft/semantic-kernel/tree/main/prompts/samples/ChildrensBookPlugin/BookIdeas',
                },
                {
                    title: 'Novel Outline',
                    uri: 'https://github.com/microsoft/semantic-kernel/tree/main/prompts/samples/WriterPlugin/NovelOutline',
                },
                {
                    title: 'Create Book',
                    uri: 'https://github.com/microsoft/semantic-kernel/tree/main/prompts/samples/ChildrensBookPlugin/CreateBook',
                },
                {
                    title: 'Summarize',
                    uri: 'https://github.com/microsoft/semantic-kernel/tree/main/prompts/samples/SummarizePlugin/Summarize',
                },
                {
                    title: 'Translate',
                    uri: 'https://github.com/microsoft/semantic-kernel/tree/main/prompts/samples/WriterPlugin/Translate',
                },
                {
                    title: 'Rewrite',
                    uri: 'https://github.com/microsoft/semantic-kernel/tree/main/prompts/samples/WriterPlugin/Rewrite',
                },
            ],
        },
        {
            header: 'Learn more about',
            items: [
                {
                    title: 'Planner',
                    uri: 'https://aka.ms/sk/concepts/planner',
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
                <Subtitle1 as="h1">Book Creator Sample App</Subtitle1>
            </div>

            {appState === AppState.ProbeForFunction ? (
                <FunctionProbe
                    uri={process.env.REACT_APP_FUNCTION_URI as string}
                    onFunctionFound={() => setAppState(AppState.Setup)}
                />
            ) : null}

            <div
                style={{
                    display: 'flex',
                    flexDirection: 'row',
                    flex: 1,
                    gap: 10,
                    alignContent: 'start',
                    justifyContent: 'space-between',
                }}
            >
                <div id="content">
                    {appState === AppState.ProbeForFunction ? null : (
                        <TabList
                            style={{ paddingTop: 60, paddingLeft: 20 }}
                            selectedValue={selectedTabValue}
                            defaultSelectedValue="setup"
                            vertical
                            size="large"
                            onTabSelect={(_, data) => changeTabValue(data.value as string)}
                        >
                            <Tab value="setup">Setup</Tab>
                            <Tab value="interact" disabled={appState < AppState.Interact}>
                                Topics
                            </Tab>
                            <Tab value="createbook" disabled={appState < AppState.CreateBook}>
                                Book
                            </Tab>
                        </TabList>
                    )}
                    <div id="main">
                        {appState === AppState.Setup ? (
                            <ServiceConfig
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                onConfigComplete={(config) => {
                                    setKeyConfig(config);
                                    setAppState(AppState.Interact);
                                }}
                            />
                        ) : null}

                        {appState === AppState.Interact ? (
                            <TopicSelection
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                keyConfig={keyConfig!}
                                onTopicSelected={(title, detail) => {
                                    setTitle(title);
                                    setDescription(detail);
                                    setAppState(AppState.CreateBook);
                                }}
                                onBack={() => {
                                    changeAppState(appState - 1);
                                }}
                            />
                        ) : null}

                        {appState === AppState.CreateBook ? (
                            <CreateBookWithPlanner
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                keyConfig={keyConfig!}
                                title={title!}
                                description={description!}
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
