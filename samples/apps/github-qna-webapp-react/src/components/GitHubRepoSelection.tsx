// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Spinner, Title3, Tooltip } from '@fluentui/react-components';
import { InfoLabel } from '@fluentui/react-components/unstable';
import { ArrowDownload16Regular, CheckmarkCircle20Filled, ErrorCircle20Regular, Info24Regular } from '@fluentui/react-icons';
import { FC, useEffect, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';

interface IData {
    uri: string;
    keyConfig: IKeyConfig;
    prevProject: string;
    prevBranch: string;
    onBack: () => void;
    onLoadProject: (project: string, branch: string) => void;
}

const enum DownloadState {
    Setup = 0,
    Loading = 1,
    Loaded = 2,
    Error = 3,
}

const GitHubTokenInformationButton: React.FC = () => {
    const openLink = () => {
        window.open("https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens", '_blank');
    };

    return (
        <Tooltip content="More information about GitHub Personal Tokens" relationship="label">
            <Button size="small" icon={<Info24Regular />} onClick={openLink} />
        </Tooltip>
    );
};

const GitHubProjectSelection: FC<IData> = ({ uri, keyConfig, prevProject, prevBranch, onLoadProject, onBack }) => {
    const [project, setProject] = useState<string>(prevProject);
    const [branch, setBranch] = useState<string>(prevBranch);
    const [patToken, setToken] = useState<string>('');
    const [downloadState, setDownloadState] = useState<DownloadState>(DownloadState.Setup);
    const sk = useSemanticKernel(uri);

    const isSameProjectAndBranch = () => {
        return project === prevProject && branch === prevBranch && project !== '' && branch !== '';
    };

    const download = async () => {
        try {
            setDownloadState(DownloadState.Loading);
            var result = await sk.invokeAsync(
                keyConfig,
                {
                    value: project || '',
                    inputs: [
                        { key: 'repositoryBranch', value: branch || '' },
                        { key: 'patToken', value: patToken || '' },
                        { key: 'searchPattern', value: '*.md' },
                    ],
                },
                'GitHubPlugin',
                'SummarizeRepository',
            );
            setDownloadState(DownloadState.Loaded);
            console.log(result);
        } catch (e) {
            setDownloadState(DownloadState.Error);
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    useEffect(() => {
        if (isSameProjectAndBranch()) {
            setDownloadState(DownloadState.Loaded);
        }
        else {
            setDownloadState(DownloadState.Setup);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [project]);

    useEffect(() => {
        if (isSameProjectAndBranch()) {
            setDownloadState(DownloadState.Loaded);
        }
        else {
            setDownloadState(DownloadState.Setup);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [branch]);

    return (
        <div style={{ paddingTop: 20, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3 style={{ alignItems: 'left' }}>GitHub Repository</Title3>
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
                    onChange={(e) => {
                        setProject(e.target.value);
                    }}
                    placeholder="https://github.com/microsoft/semantic-kernel"
                />
            </div>
            <Label>
                <strong>GitHub Personal Access Token (optional)</strong>
                <GitHubTokenInformationButton />
            </Label>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
                <Input
                    style={{ width: '100%' }}
                    type="password"
                    value={patToken}
                    onChange={(e) => {
                        setToken(e.target.value);
                    }}
                    placeholder=""
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
                    onChange={(e) => {
                        setBranch(e.target.value);
                    }}
                    placeholder="main"
                />
                <Button
                    disabled={
                        project === '' ||
                        branch === '' ||
                        downloadState === DownloadState.Loading ||
                        downloadState === DownloadState.Loaded
                    }
                    appearance="transparent"
                    icon={<ArrowDownload16Regular />}
                    onClick={() => download()}
                />
            </div>
            <div style={{ display: 'flex', flexDirection: 'row' }}>
                <Label>
                    <strong>Embedding File Types</strong>
                </Label>
                <InfoLabel
                    info={
                        <div style={{ maxWidth: 250 }}>
                            Embedding and answers will be based on the files of the type indicated below.
                        </div>
                    }
                    htmlFor={`EmbeddingFileTypeTooltip`}
                />
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
                <Input
                    readOnly
                    disabled
                    style={{ width: '100%' }}
                    type="text"
                    value="*.md"
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
