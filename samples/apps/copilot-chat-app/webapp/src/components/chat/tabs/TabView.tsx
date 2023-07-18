// Copyright (c) Microsoft. All rights reserved.

import { Label, Link, makeStyles, shorthands } from '@fluentui/react-components';
import { tokens } from '@fluentui/tokens';
import { SharedStyles } from '../../../styles';

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...SharedStyles.scroll,
        display: 'flex',
        flexDirection: 'column',
    },
    footer: {
        paddingTop: tokens.spacingVerticalL,
    },
});

interface ITabViewProps {
    title: string;
    learnMoreDescription: string;
    learnMoreLink: string;
    children?: React.ReactNode;
}

export const TabView: React.FC<ITabViewProps> = ({ title, learnMoreDescription, learnMoreLink, children }) => {
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <h2>{title}</h2>
            {children}
            <Label size="small" color="brand" className={classes.footer}>
                Want to learn more about {learnMoreDescription}? Click{' '}
                <Link href={learnMoreLink} target="_blank" rel="noreferrer">
                    here
                </Link>
                .
            </Label>
        </div>
    );
};
