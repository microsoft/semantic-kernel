// Copyright (c) Microsoft. All rights reserved.

import { Spinner } from '@fluentui/react-components';
import { FC } from 'react';

interface ILoadingProps {
    text: string;
}

const Loading: FC<ILoadingProps> = ({ text }) => {
    return (
        <div style={{ padding: 80, alignItems: 'center' }}>
            <Spinner labelPosition="below" label={text} />
        </div>
    );
};

export default Loading;
