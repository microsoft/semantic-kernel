// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Input, Label, Spinner, Subtitle2, Title3 } from '@fluentui/react-components';
import { ArrowDownload16Regular, CheckmarkCircle20Filled } from '@fluentui/react-icons';
import { FC, useState } from "react";
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';

interface IData {
    uri: string;
    keyConfig: IKeyConfig;
    onBack: () => void;
    onLoadProject: (project: string, branch: string) => void;
}

const GitHubProjectSelection: FC<IData> = ({ uri, keyConfig, onLoadProject, onBack }) => {
    const [project, setProject] = useState<string>();
    const [branch, setBranch] = useState<string>();
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isLoaded, setIsLoaded] = useState<boolean>(false);
    const [isLoadError, setIsLoadError] = useState<boolean>(false);
    const sk = useSemanticKernel(uri);
    
    const download = async () => {
        const url = `${project}/archive/refs/heads${branch}.zip`;
        const path = `%temp%\\${project}-${branch}.zip`;

        try {
            var result = await sk.invokeAsync(keyConfig, { value: url, inputs: [{ key: 'filePath', value: path }] }, 'WebFileDownloadSkill', 'DownloadToFile');
            setIsLoaded(true);
        } catch {
            setIsLoadError(true);
            alert('Something went wrong. Please check that the function is running and accessible from this location.');
        }
    }

    return (
        <div style={{ paddingTop: 20, gap: 20, display: "flex", flexDirection: "column", alignItems: "left" }}>
            <Title3 style={{ alignItems: 'left' }}>Enter in the GitHub Project URL</Title3>
            <Subtitle2>Start by entering a GitHub Repository URL. We will pull the public repository into local memory so you can ask any questions about the repository and get help. </Subtitle2>
            <br></br>
            <Label><strong>GitHub Repository URL</strong></Label>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
                <Input style={{ width: '100%' }} type="text" value={project} onChange={(e) => setProject(e.target.value)} placeholder="https://github.com/microsoft/semantic-kernel"/>
            </div>
            <Label><strong>Branch Name</strong></Label>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10 }}>
                <Input style={{ width: '100%' }} type="text" value={branch} onChange={(e) => setBranch(e.target.value)} placeholder="main" />
                <Button disabled={project === undefined || branch === undefined} appearance='transparent' icon={<ArrowDownload16Regular />} onClick={() => download()}/>
            </div>
            {isLoading ?
                <div>
                    <Spinner />
                    <Body1>
                        Downloading respository...
                    </Body1>
                </div>
                :
                <></>
            }
            {isLoaded ?
            <div>
                    <CheckmarkCircle20Filled />
                    <Body1>
                        Repository downloaded. You can ask questions about it on the next page.
                    </Body1>
                </div> : <></>}
            {isLoadError ?
                <div>
                    <Body1>
                        There was an error downloading the repository. Please try again.
                    </Body1>
                </div>
                :
                <></>
            }
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'left', gap: 20 }}>
                <Button style={{ width: 54 }} appearance="secondary" onClick={() => onBack()}>Back</Button>
                <Button disabled={!isLoaded} appearance="primary" onClick={() => { if (project !== undefined && branch !== undefined) onLoadProject(project, branch) }}>Next</Button>
            </div>
        </div>
    );
};

export default GitHubProjectSelection;