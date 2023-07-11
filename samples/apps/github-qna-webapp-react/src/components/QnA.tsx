// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Label, Slider, SliderOnChangeData, Title3 } from '@fluentui/react-components';
import { InfoLabel } from '@fluentui/react-components/unstable';
import React, { FC, useCallback, useState } from 'react';
import { ChatHistoryItem, FetchState, IChatMessage } from './chat/ChatHistoryItem';

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
                `Hi! I'm your GitHub Repo bot. Here's the repo you are interested in: <a href=${project}>` +
                project +
                '</a>. How can I help you to learn more about this repo? ',
            author: 'GitHub Repo Bot',
            timestamp: new Date().toISOString(),
            mine: false,
        },
    ]);
    const [response, setResponse] = useState<IChatMessage>();

    const [relevance, setRelevance] = useState(0.4);
    const onSliderChange = useCallback((_e: any, sliderData: SliderOnChangeData) => {
        setRelevance(sliderData.value);
    }, []);

    const getResponse = async (m: IChatMessage) => {
        const projectUri = project.endsWith('/') ? project.substring(0, project.length - 1) : project;
        const response: IChatMessage = {
            content: '',
            author: 'GitHub Repo Bot',
            timestamp: new Date().toISOString(),
            mine: false,
            fetchState: FetchState.Fetching,
            index: chatHistory.length + 1,
        };
        setChatHistory([...chatHistory, m, response]);
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
                'GitHubMemoryQuery',
            );
            response.content = result.value;
            response.fetchState = FetchState.Fetched;
            return response;
        } catch (e) {
            response.content = `Something went wrong. Please try again.\nDetails: {${e}}`;
            response.fetchState = FetchState.Error;
            return response;
        }
    };

    React.useEffect(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [isBusy, response, chatHistory]);

    React.useEffect(() => {
        if (response) {
            if (response.index) chatHistory[response.index] = response;
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
                        marginBottom: 12,
                    }}
                >
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
                        <Label size="small">No Threshold</Label>
                        <Slider min={0} max={1} step={0.1} value={relevance} onChange={onSliderChange} />
                        <Label size="small">Perfect Match</Label>
                    </div>
                    <InfoLabel
                        info={
                            <div style={{ maxWidth: 250 }}>
                                'Relevance' is used in memory search and is a measure from 0.0 to 1.0, where 1.0 means a
                                perfect match. We encourage users to experiment with different values to see what the
                                model thinks is most relevant to the query.
                            </div>
                        }
                        htmlFor={`RelevanceTooltip`}
                    >
                        Relevance Threshold
                    </InfoLabel>
                </div>
            </div>
        </div>
    );
};

export default QnA;
