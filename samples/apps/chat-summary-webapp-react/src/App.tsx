// Copyright (c) Microsoft. All rights reserved.

import { Subtitle1, Tab, TabList } from '@fluentui/react-components';
import { FC, useEffect, useState } from 'react';
import AISummary from './components/AISummary';
import ChatInteraction from './components/chat/ChatInteraction';
import { IChatMessage } from './components/chat/ChatThread';
import FunctionProbe from './components/FunctionProbe';
import QuickTips, { ITipGroup } from './components/QuickTips';
import ServiceConfig from './components/ServiceConfig';
import { IKeyConfig } from './model/KeyConfig';

const App: FC = () => {
    enum AppState {
        ProbeForFunction = 0,
        Setup = 1,
        Interact = 2,
        GetAISummary = 3,
    }

    const appStateToTabValueMap = new Map<AppState, string>([
        [AppState.Setup, 'setup'],
        [AppState.Interact, 'interact'],
        [AppState.GetAISummary, 'aisummary'],
    ]);
    const tabValueToAppStateMap = new Map<string, AppState>([
        ['setup', AppState.Setup],
        ['interact', AppState.Interact],
        ['aisummary', AppState.GetAISummary],
    ]);

    const [keyConfig, setKeyConfig] = useState<IKeyConfig>();
    const [appState, setAppState] = useState<AppState>(AppState.ProbeForFunction);
    const [selectedTabValue, setSelectedTabValue] = useState<string>('setup');
    const [chat, setChat] = useState<IChatMessage[]>();

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
                    title: 'Summarize',
                    uri: 'https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Skills/Skills.Core/ConversationSummarySkill.cs#L70',
                },
                {
                    title: 'Action Items',
                    uri: 'https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Skills/Skills.Core/ConversationSummarySkill.cs#L87',
                },
                {
                    title: 'Topics',
                    uri: 'https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Skills/Skills.Core/ConversationSummarySkill.cs#L104',
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
                <Subtitle1 as="h1">Simple Chat Summary App</Subtitle1>
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
                    gap: 10,
                    flex: 1,
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
                                Interact
                            </Tab>
                            <Tab value="aisummary" disabled={appState < AppState.GetAISummary}>
                                AI Summaries
                            </Tab>
                        </TabList>
                    )}
                    <div id="main">
                        {appState === AppState.Setup ? (
                            <ServiceConfig
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                onConfigComplete={(keyConfig) => {
                                    setKeyConfig(keyConfig);
                                    setAppState(AppState.Interact);
                                }}
                            />
                        ) : null}

                        {appState === AppState.Interact ? (
                            <ChatInteraction
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                onGetAISummary={(chat) => {
                                    setChat(chat);
                                    setAppState(AppState.GetAISummary);
                                }}
                                onBack={() => {
                                    changeAppState(appState - 1);
                                }}
                            />
                        ) : null}

                        {appState === AppState.GetAISummary && chat !== undefined ? (
                            <AISummary
                                uri={process.env.REACT_APP_FUNCTION_URI as string}
                                keyConfig={keyConfig!}
                                chat={chat}
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
