import { makeStyles } from '@fluentui/react-components';

export const useDialogClasses = makeStyles({
    root: {
        height: '515px',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        rowGap: '10px',
    },
    scopes: {
        display: 'flex',
        flexDirection: 'column',
        rowGap: '5px',
        paddingLeft: '20px',
    },
    error: {
        color: '#d13438',
    },
    section: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        rowGap: '10px',
    },
    footer: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        minWidth: '175px',
    },
});
