// Copyright (c) Microsoft. All rights reserved.

import { Link, Subtitle2 } from '@fluentui/react-components';
import { FC } from 'react';
import { ITipGroup } from './QuickTips';

interface IData {
    tipGroup: ITipGroup;
}

const QuickTipGroup: FC<IData> = ({ tipGroup }) => {
    return (
        <div
            style={{
                backgroundColor: 'white',
                paddingLeft: 10,
                paddingTop: 20,
                paddingBottom: 20,
                gap: 10,
                width: 278,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'start',
            }}
        >
            <Subtitle2>{tipGroup.header}</Subtitle2>
            {tipGroup.items.map((t, idx) => (
                <Link key={idx} style={{ color: '#115EA3' }} href={t.uri} target="_blank" rel="noreferrer">
                    {t.title}
                </Link>
            ))}
        </div>
    );
};

export default QuickTipGroup;
