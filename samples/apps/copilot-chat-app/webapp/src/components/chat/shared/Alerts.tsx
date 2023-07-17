// Copyright (c) Microsoft. All rights reserved.

import {
    makeStyles,
    tokens
} from '@fluentui/react-components';
import { Alert } from '@fluentui/react-components/unstable';
import { Dismiss16Regular } from '@fluentui/react-icons';
import React from 'react';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { RootState } from '../../../redux/app/store';
import { removeAlert } from '../../../redux/features/app/appSlice';

const useClasses = makeStyles({
    root: {
    },
    alert: {
        fontWeight: tokens.fontWeightRegular,
        color: tokens.colorNeutralForeground1,
        backgroundColor: tokens.colorNeutralBackground6,
        fontSize: tokens.fontSizeBase200,
        lineHeight: tokens.lineHeightBase200,
    },
});

export const Alerts: React.FC = () => {
    const classes = useClasses();
    const dispatch = useAppDispatch();
    const { alerts } = useAppSelector((state: RootState) => state.app);

    return (
        <div className={classes.root}>
            {alerts.map(({ type, message }, index) => {
                return (
                    <Alert
                        intent={type}
                        action={{
                            icon: (
                                <Dismiss16Regular
                                    aria-label="dismiss message"
                                    onClick={() => {
                                        dispatch(removeAlert(index));
                                    }}
                                    color="black"
                                />
                            ),
                        }}
                        key={`${index}-${type}`}
                        className={classes.alert}
                    >
                        {message.slice(0, 1000) + (message.length > 1000 ? '...' : '')}
                    </Alert>
                );
            })}
        </div>
    );
};
