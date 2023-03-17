// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Spinner, Title3 } from '@fluentui/react-components';
import { ArrowDownload16Regular, CheckmarkCircle20Filled, ErrorCircle20Regular } from '@fluentui/react-icons';
import { FC, useEffect, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';

interface IData {
    uri: string;
    keyConfig: IKeyConfig;
    onBack: () => void;
    onLoadProject: (project: string, branch: string) => void;
}

const enum DownloadState {
    Setup = 0,
    Loading = 1,
    Loaded = 2,
    Error = 3,
}

const GitHubProjectSelection: FC<IData> = ({ uri, keyConfig, onLoadProject, onBack }) => {
    const [project, setProject] = useState<string>();
    const [branch, setBranch] = useState<string>();
    const [downloadState, setDownloadState] = useState<DownloadState>(DownloadState.Setup);
    const sk = useSemanticKernel(uri);

    const download = async () => {
        try {
            setDownloadState(DownloadState.Loading);
            var result = await sk.invokeAsync(
                keyConfig,
                {
                    value: project || '',
                    inputs: [
                        { key: 'repositoryBranch', value: branch || '' },
                        { key: 'searchPattern', value: '*.md' },
                    ],
                },
                'GitHubSkill',
                'SummarizeRepository',
            );
            setDownloadState(DownloadState.Loaded);
            console.log(result);
        } catch (e) {
            setDownloadState(DownloadState.Error);
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    let DownloadStatus = <></>;
    useEffect(() => {
        switch (downloadState) {
            case DownloadState.Loading:
                DownloadStatus = (
                    <>
                        <Spinner size="extra-small" />
                        <Body1>
                            Summarizing repository markdown files. Please wait, this can take several minutes depending
                            on the number of files.
                        </Body1>
                    </>
                );
                break;
            case DownloadState.Loaded:
                DownloadStatus = (
                    <>
                        <CheckmarkCircle20Filled color="green" />
                        <Body1>
                            Repository markdown files summarized. You can ask questions about it on the next page.
                        </Body1>
                    </>
                );
                break;
            case DownloadState.Error:
                DownloadStatus = (
                    <>
                        <ErrorCircle20Regular color="red" />
                        <Body1>There was an error summarizing the repository. Please try again.</Body1>
                    </>
                );
                break;
        }
    }, [downloadState]);

    return (
        <div style={{ paddingTop: 20, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3 style={{ alignItems: 'left' }}>Enter in the GitHub Project URL</Title3>
            <Body1>
                Start by entering a GitHub Repository URL. We will pull the public repository into local memory so you
                can ask any questions about the repository and get help.{' '}
            </Body1>
            <br></br>
            <Label>
                <strong>GitHub Repository URL</strong>
            </Label>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
                <Input
                    style={{ width: '100%' }}
                    type="text"
                    value={project}
                    onChange={(e) => setProject(e.target.value)}
                    placeholder="https://github.com/microsoft/semantic-kernel"
                />
            </div>
            <Label>
                <strong>Branch Name</strong>
            </Label>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
                <Input
                    style={{ width: '100%' }}
                    type="text"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="main"
                />
                <Button
                    disabled={project === undefined || branch === undefined || downloadState === DownloadState.Loading}
                    appearance="transparent"
                    icon={<ArrowDownload16Regular />}
                    onClick={() => download()}
                />
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10, alignItems: 'center' }}>
                {downloadState === DownloadState.Loading ? (
                    <>
                        <Spinner size="tiny" />
                        <Body1>
                            Downloading repository. Please wait, this can take several minutes depending on the number
                            of files.
                        </Body1>
                    </>
                ) : downloadState === DownloadState.Loaded ? (
                    <>
                        <CheckmarkCircle20Filled color="green" />
                        <Body1>Repository downloaded. You can learn more about it on the next page.</Body1>
                    </>
                ) : downloadState === DownloadState.Error ? (
                    <>
                        <ErrorCircle20Regular color="red" />
                        <Body1>There was an error downloading the repository. Please try again.</Body1>
                    </>
                ) : null}
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'left', gap: 20 }}>
                <Button style={{ width: 54 }} appearance="secondary" onClick={() => onBack()}>
                    Back
                </Button>
                <Button
                    disabled={downloadState !== DownloadState.Loaded}
                    appearance="primary"
                    onClick={() => {
                        if (project !== undefined && branch !== undefined) onLoadProject(project, branch);
                    }}
                >
                    Next
                </Button>
            </div>
        </div>
    );
};

export default GitHubProjectSelection;
