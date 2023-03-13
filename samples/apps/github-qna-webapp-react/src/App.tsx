// Copyright (c) Microsoft. All rights reserved.

import { Subtitle1, Tab, TabList } from '@fluentui/react-components';
import { FC, useEffect, useState } from 'react';
import FunctionProbe from './components/FunctionProbe';
import GitHubProjectSelection from './components/GitHubRepoSelection';
import QnA from './components/QnA';
import QuickTips, { ITipGroup } from './components/QuickTips';
import ServiceConfig from './components/ServiceConfig';
import { IKeyConfig } from './model/KeyConfig';

const App: FC = () => {

  enum AppState {
    ProbeForFunction = 0,
    Setup = 1,
    GitHubProject = 2,
    QnA = 3
  }

  const appStateToTabValueMap = new Map<AppState, string>([
    [AppState.Setup, "setup"],
    [AppState.GitHubProject, "github"],
    [AppState.QnA, "qna"]
  ]);
  const tabValueToAppStateMap = new Map<string, AppState>([
    ["setup", AppState.Setup],
    ["github", AppState.GitHubProject],
    ["qna", AppState.QnA]
  ]);

  const [keyConfig, setKeyConfig] = useState<IKeyConfig>();
  const [appState, setAppState] = useState<AppState>(AppState.ProbeForFunction);
  const [selectedTabValue, setSelectedTabValue] = useState<string>("setup");
  const [project, setProject] = useState<string>();
  const [branch, setBranch] = useState<string>();

  useEffect(() => {
    changeAppState(appState);
    // eslint-disable-next-line react-hooks/exhaustive-deps   
  }, [appState]);

  const changeAppState = function (newAppState: AppState) {
    setAppState(newAppState);
    setSelectedTabValue(appStateToTabValueMap.get(newAppState) ?? "setup");
  }
  const changeTabValue = function (newTabValue: string) {
    setSelectedTabValue(newTabValue)
    setAppState(tabValueToAppStateMap.get(newTabValue) ?? AppState.Setup);
  }

  const tips: ITipGroup[] = [
    {
      header: 'Useful Resources',
      items: [
        {
          title: 'Read Documentation',
          uri: 'https://aka.ms/SKDocBook'
        }
      ]
    },
    {
      header: 'Functions used in this sample',
      items: [
        {
          title: 'Q&A',
          uri: '#TODO'
        },
        {
          title: 'Pull Web Content',
          uri: '#TODO'
        },
      ]
    },
    {
      header: 'Learn more about',
      items: [
        {
          title: 'Memories',
          uri: '#TODO'
        },
        {
          title: 'Embeddings',
          uri: '#TODO'
        },
      ]
    },
    {
      header: 'Local SK URL',
      items: [
        {
          title: process.env.REACT_APP_FUNCTION_URI as string,
          uri: process.env.REACT_APP_FUNCTION_URI as string
        }
      ]
    }
  ];

  return (
    <div id='container' style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <div id="header">
        <Subtitle1 as='h1'>GitHub Repo Q&A Bot</Subtitle1>
      </div>

      {appState === AppState.ProbeForFunction ?
        <FunctionProbe uri={process.env.REACT_APP_FUNCTION_URI as string} onFunctionFound={() => setAppState(AppState.Setup)} /> :
        null}

      <div style={{
        display: 'flex',
        flexDirection: 'row',
        gap: 10,
        flex: 1,
        height: '90vh',
        alignContent: 'start',
        justifyContent: 'space-between'
      }}>
        <div id='content'>
          {appState === AppState.ProbeForFunction ? null :
            <TabList
              style={{ paddingTop: 60, paddingLeft: 20 }}
              selectedValue={selectedTabValue}
              defaultSelectedValue='setup'
              vertical
              size='large'
              onTabSelect={(_, data) => changeTabValue(data.value as string)}>
              <Tab value="setup">Setup</Tab>
              <Tab value="github" disabled={appState < AppState.GitHubProject}>GitHub Repository</Tab>
              <Tab value="qna" disabled={appState < AppState.QnA}>Q&A</Tab>
            </TabList>
          }
          <div id='main'>
            {appState === AppState.Setup ?
              <ServiceConfig uri={process.env.REACT_APP_FUNCTION_URI as string} onConfigComplete={(keyConfig) => { setKeyConfig(keyConfig); setAppState(AppState.GitHubProject); }} /> :
              null}

            {appState === AppState.GitHubProject ?
              <GitHubProjectSelection
                keyConfig={keyConfig!}
                uri={process.env.REACT_APP_FUNCTION_URI as string}
                onLoadProject={(project, branch) => { setProject(project); setBranch(branch); setAppState(AppState.QnA) }}
                onBack={() => { changeAppState(appState - 1) }} /> :
              null}

            {appState === AppState.QnA && project !== undefined && branch !== undefined ?
              <QnA uri={process.env.REACT_APP_FUNCTION_URI as string} keyConfig={keyConfig!} project={project} branch={branch} onBack={() => { changeAppState(appState - 1) }} /> :
              null}
          </div>

        </div>
        {appState === AppState.ProbeForFunction ? null : <div id='tipbar'>
          <QuickTips tips={tips} />
        </div>}
      </div>
    </div>
  );
}

export default App;
