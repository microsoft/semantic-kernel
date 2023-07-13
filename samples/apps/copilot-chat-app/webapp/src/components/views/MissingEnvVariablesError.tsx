// Copyright (c) Microsoft. All rights reserved.

import { Body1, Subtitle1, Title3 } from '@fluentui/react-components';
import { FC } from 'react';
import { useClasses } from '../../App';

interface IData {
    missingVariables: string[];
}

const MissingEnvVariablesError: FC<IData> = ({ missingVariables }) => {
    const classes = useClasses();

    return (
        <div className={classes.container}>
            <div className={classes.header}>
                <Subtitle1 as="h1">Copilot Chat</Subtitle1>
            </div>
            <div style={{ padding: 80, gap: 20, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <Title3>
                    {'Please ensure your ".env" file is set up correctly with all environment variables defined in ".env.example" then restart the app.'}
                </Title3>
                <Body1>You are missing the following variables: {missingVariables.join(', ')}</Body1>
            </div>
        </div>
    );
};

export default MissingEnvVariablesError;
