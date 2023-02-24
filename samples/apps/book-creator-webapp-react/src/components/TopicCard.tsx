// Copyright (c) Microsoft. All rights reserved.

import { Body1, Button, Title3 } from '@fluentui/react-components';
import { FC } from 'react';

interface IData {
    title: string;
    detail: string;

    onSelect: (title: string, detail: string) => void;
}

const TopicCard: FC<IData> = ({ title, detail, onSelect }) => {
    return (
        <div
            style={{ padding: 10, gap: 5, width: 350, display: 'flex', flexDirection: 'column', alignItems: 'center' }}
        >
            <Title3>{title}</Title3>
            <Body1 wrap style={{ maxWidth: 300 }}>
                {detail}
            </Body1>
            <Button appearance="primary" onClick={() => onSelect(title, detail)}>
                Select
            </Button>
        </div>
    );
};

export default TopicCard;
