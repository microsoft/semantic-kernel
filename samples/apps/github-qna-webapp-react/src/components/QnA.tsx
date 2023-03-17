// Copyright (c) Microsoft. All rights reserved.

import { Avatar, Body1, Button, Label, Slider, SliderOnChangeData, Title3 } from '@fluentui/react-components';
import React, { FC, useCallback, useState } from 'react';
import { ChatHistoryItem, IChatMessage } from './chat/ChatHistoryItem';

import GithubAvatar from '../assets/icons8-github-512.png';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';
import { ChatInput } from './chat/ChatInput';

interface IData {
    uri: string;
    project: string;
    branch: string;
    keyConfig: IKeyConfig;
    onBack: () => void;
}

const QnA: FC<IData> = ({ uri, project, branch, keyConfig, onBack }) => {
    const sk = useSemanticKernel(uri);

    const chatBottomRef = React.useRef<HTMLDivElement>(null);
    const [isBusy, setIsBusy] = useState<boolean>();
    const [chatHistory, setChatHistory] = useState<IChatMessage[]>([
        {
            content:
                "Hi! I'm your GitHub Repo bot. Here's the repo you are interested in: <a href={project}>" +
                project +
                '</a>',
            author: 'GitHub Repo Bot',
            timestamp: new Date().toISOString(),
            mine: false,
        },
    ]);
    const [response, setResponse] = useState<IChatMessage>();

    const [relevance, setRelevance] = useState(0.2);
    const onSliderChange = useCallback((_e: any, sliderData: SliderOnChangeData) => {
        setRelevance(sliderData.value);
    }, []);

    const getResponse = async (m: IChatMessage) => {
        const projectUri = project.endsWith('/') ? project.substring(0, project.length - 1) : project;

        try {
            var result = await sk.invokeAsync(
                keyConfig,
                {
                    value: m.content,
                    inputs: [
                        { key: 'relevance', value: relevance.toString() },
                        { key: 'collection', value: `${projectUri}-${branch}` },
                    ],
                },
                'QASkill',
                'MemoryQuery',
            );
            const response: IChatMessage = {
                content: result.value,
                author: 'GitHub Repo Bot',
                timestamp: new Date().toISOString(),
                mine: false,
            };
            return response;
        } catch (e) {
            alert('Something went wrong.\n\nDetails:\n' + e);
        }
    };

    React.useEffect(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [isBusy]);

    React.useEffect(() => {
        if (response) {
            setChatHistory([...chatHistory, response]);
            setIsBusy(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [response]);

    return (
        <div style={{ paddingTop: 20, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3>Ask questions about the repository</Title3>
            <Body1>
                Now that the repository is in your local memory and embeddings are created for it, you can ask questions
                about it.
            </Body1>

            <div
                style={{
                    position: 'relative',
                    maxHeight: '690px',
                    maxWidth: '1052px',
                    display: 'grid',
                    gridTemplateColumns: 'minmax(300px, 800px)',
                    gridTemplateRows: 'auto 1fr auto',
                    gridTemplateAreas: "'menu' 'content' 'footer'",
                    justifyContent: 'center',
                    boxShadow: '0 2px 4px 0 lightgray',
                    padding: '2% 5% 2%',
                }}
            >
                <div
                    style={{
                        gridArea: 'content',
                        overflowY: 'auto',
                        overflowX: 'hidden',
                        padding: '1rem 0',
                        height: '500px',
                        display: 'flex',
                        flexDirection: 'row',
                        gap: 10,
                    }}
                >
                    <Avatar
                        image={{
                            src: GithubAvatar,
                        }}
                        color="neutral"
                        badge={{ status: 'available' }}
                    />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {chatHistory.map((m, idx) => (
                            <ChatHistoryItem key={idx} message={m} />
                        ))}
                        <div ref={chatBottomRef} />
                    </div>
                </div>
                <div style={{ gridArea: 'footer', padding: '1rem 0', borderTop: '1px solid #ccc' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        <ChatInput
                            onSubmit={async (m) => {
                                setIsBusy(true);
                                setChatHistory([...chatHistory, m]);
                                const response = await getResponse(m);
                                setResponse(response!);
                                setIsBusy(false);
                            }}
                        />
                    </div>
                </div>
            </div>

            <div
                style={{
                    display: 'flex',
                    flexDirection: 'row',
                    alignItems: 'left',
                    gap: '20',
                    justifyContent: 'space-between',
                    marginTop: 20,
                }}
            >
                <Button onClick={() => onBack()} style={{ height: 'fit-content' }}>
                    Back
                </Button>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginRight: '5%' }}>
                    <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center' }}>
                        <Label size="small">0</Label>
                        <Slider min={0} max={1} step={0.1} value={relevance} onChange={onSliderChange} />
                        <Label size="small">1</Label>
                    </div>
                    <Label size="medium">Relevance: {relevance}</Label>
                </div>
            </div>
        </div>
    );
};

export default QnA;
