// Copyright (c) Microsoft. All rights reserved.

import React, { FC } from 'react';
import { Subtitle1 } from '@fluentui/react-components';
import { Lightbulb24Regular } from '@fluentui/react-icons';
import QuickTipGroup from './QuickTipGroup';

interface ITipItem {
    title: string;
    uri: string;
}

export interface ITipGroup {
    header: string;
    items: ITipItem[];
}

interface IData {
    tips: ITipGroup[]
}

const QuickTips: FC<IData> = ({ tips }) => {

    return (
        <div style={{ paddingTop: 48, paddingLeft: 36, paddingBottom: 2, gap: 15, display: 'flex', flexDirection: 'column', alignItems: 'start' }}>
            <div style={{ display: 'flex', flexDirection: 'row', gap: 10, alignItems: 'center' }}>
                <Lightbulb24Regular color='#AA0055' filled /><Subtitle1>Quick Tips</Subtitle1>
            </div>

            <div>
                <hr style={{ width: 288, color: '#E0E0E0' }} />
            </div>
            {tips.map((t, idx) => <QuickTipGroup key={idx} tipGroup={t} />)}
        </div>
    );
}

export default QuickTips;