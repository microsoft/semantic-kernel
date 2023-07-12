import { Textarea, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import * as React from 'react';
import { SharedStyles } from '../../styles';
interface ChatPersonaProps {
    chatId: string;
}

const useClasses = makeStyles({
    root: {
        ...shorthands.margin(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        ...SharedStyles.scroll,
    },
    table: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tableHeader: {
        fontWeight: tokens.fontSizeBase600,
    },
});

export const ChatPersona: React.FC<ChatPersonaProps> = ({ chatId }) => {
    const classes = useClasses();
    return (
        <div className={classes.root}>
            <h2>Persona</h2>
            <p>Chat ID: {chatId} -- not necessary. </p>{' '}
            <p>
                List all the persona-related information which includes: 1/ meta prompt for the chat bot, 2/ short term
                memory (this is supposed to be in here somewhere), 3/ long term memory so that a user can edit it. Think
                of it as a way to give the chat session a *lobotomy* ...
            </p>
            <h3>Meta Prompt</h3>
            <p>Extend this box so it is wide please</p>
            <Textarea placeholder="I am a well-behaved chat bot that will not go out off on tangents." />
            <h3>Short Term Memory</h3>
            <p>
                Explanation: We maintain a summary of the most recent N chat exchanges. Based upon intent, this memory
                will be preferred based upon the meta-prompt.
            </p>
            <Textarea placeholder="The things that I'm holding on to from our chat that's most recent and salient." />
            <h3>Long Term Memory</h3>
            <p>
                Explanation: We maintain a summary of the least recent N chat exchanges. Based upon intent, this memory
                will be preferred based upon the meta-prompt.
            </p>
            <Textarea placeholder="Things that I'll need in the future but don't need now." />
        </div>
    );
};
