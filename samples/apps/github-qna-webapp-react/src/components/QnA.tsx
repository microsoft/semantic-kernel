// Copyright (c) Microsoft. All rights reserved.

import { Button, Label, Slider, SliderOnChangeData, Subtitle2, Title3 } from '@fluentui/react-components';
import React, { FC, useCallback, useState } from 'react';
import { useSemanticKernel } from '../hooks/useSemanticKernel';
import { IKeyConfig } from '../model/KeyConfig';

import { ChatHistoryItem, IChatMessage } from './chat/ChatHistoryItem';
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
                "Hi! I'm your GitHub Repo bot. Here's the GitHub repo you selected: <a href={project}>" +
                project +
                '</a>',
            author: 'GitHub Repo Bot',
            timestamp: new Date().toISOString(),
            mine: false,
        },
    ]);

    const [relevance, setRelevance] = useState(0.2);
    const onSliderChange = useCallback((_e: any, sliderData: SliderOnChangeData) => {
        setRelevance(sliderData.value);
    }, []);

    React.useEffect(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [isBusy]);

    return (
        <div style={{ paddingTop: 20, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'left' }}>
            <Title3>Ask questions about the repository</Title3>
            <Subtitle2>
                Now that the repository is in your local memory and embeddings are created for it, you can ask questions
                about it.
            </Subtitle2>

            <div
                style={{
                    position: 'relative',
                    maxHeight: '70vh',
                    display: 'grid',
                    gridTemplateColumns: 'minmax(300px, 800px)',
                    gridTemplateRows: 'auto 1fr auto',
                    gridTemplateAreas: "'menu' 'content' 'footer'",
                    justifyContent: 'center',
                }}
            >
                <div style={{ gridArea: 'content', overflowY: 'auto', overflowX: 'hidden', padding: '1rem 0' }}>
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
                            onSubmit={(m) => {
                                setIsBusy(true);
                                setChatHistory([...chatHistory, m]);
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
