// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Spinner, Title3 } from '@fluentui/react-components';
import { ArrowDownload16Regular, CheckmarkCircle20Filled } from '@fluentui/react-icons';
import React, { FC, useState } from 'react';
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

const GitHubProjectSelection: FC<IData> = ({ uri, keyConfig, prevProject, prevBranch, onLoadProject, onBack }) => {
    const [project, setProject] = useState<string>(prevProject);
    const [branch, setBranch] = useState<string>(prevBranch);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isLoaded, setIsLoaded] = useState<boolean>(project !== '' && branch !== '');
    const [isLoadError, setIsLoadError] = useState<boolean>(false);
    const sk = useSemanticKernel(uri);

    const isSameProjectAndBranch = () => {
        return project === prevProject && branch === prevBranch && project !== '' && branch !== '';
    }

    const download = async () => {
        try {
            setIsLoading(true);
            setIsLoaded(false);
            setIsLoadError(false);
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
            setIsLoaded(true);
            console.log(result);
        } catch (e) {
            setIsLoadError(true);
            alert('Something went wrong.\n\nDetails:\n' + e);
        } finally {
            setIsLoading(false);
        }
    };

    React.useEffect(() => {
        setIsLoaded(isSameProjectAndBranch())
    }, [project]);

    React.useEffect(() => {
        setIsLoaded(isSameProjectAndBranch())
    }, [branch]);

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
                    onChange={(e) => {
                        setProject(e.target.value);
                    }}
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
                    onChange={(e) => {
                        setBranch(e.target.value);
                    }}
                    placeholder="main"
                />
                <Button
                    disabled={isLoading || isLoaded || project === '' || branch === '' }
                    appearance="transparent"
                    icon={<ArrowDownload16Regular />}
                    onClick={() => download()}
                />
            </div>
            {isLoading ? (
                <div>
                    <Spinner />
                    <Body1>
                        Summarizing repository markdown files. Please wait, this can take several minutes depending on
                        the number of files.
                    </Body1>
                </div>
            ) : (
                <></>
            )}
            {isLoaded ? (
                <div>
                    <CheckmarkCircle20Filled />
                    <Body1>
                        Repository markdown files summarized. You can ask questions about it on the next page.
                    </Body1>
                </div>
            ) : (
                <></>
            )}
            {isLoadError ? (
                <div>
                    <Body1>There was an error summarizing the repository. Please try again.</Body1>
                </div>
            ) : (
                <></>
            )}
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'left', gap: 20 }}>
                <Button style={{ width: 54 }} appearance="secondary" onClick={() => onBack()}>
                    Back
                </Button>
                <Button
                    disabled={!isLoaded}
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
