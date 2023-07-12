import { Caption1, Card, CardHeader, Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { ReactElement } from 'react';

const useClasses = makeStyles({
    main: {
        ...shorthands.gap('36px'),
        display: 'flex',
        flexDirection: 'column',
        flexWrap: 'wrap',
    },
    title: {
        ...shorthands.margin(0, 0, '12px'),
    },
    description: {
        ...shorthands.margin(0, 0, '12px'),
    },
    card: {
        width: '480px',
        maxWidth: '100%',
        height: '124px',
    },
    caption: {
        color: tokens.colorNeutralForeground3,
    },
    logo: {
        ...shorthands.borderRadius('4px'),
        width: '48px',
        height: '48px',
    },
    text: {
        ...shorthands.margin(0),
    },
});

interface IBaseCardProps {
    image?: string;
    header: string;
    secondaryText: string;
    description: string;
    action: ReactElement;
}

export const BaseCard: React.FC<IBaseCardProps> = ({ image, header, secondaryText, description, action }) => {
    const styles = useClasses();

    return (
        <Card className={styles.card}>
            <CardHeader
                image={<img className={styles.logo} src={image} alt={`${header} icon`} />}
                header={<Text weight="semibold">{header}</Text>}
                description={<Caption1 className={styles.caption}>{secondaryText}</Caption1>}
                action={action}
            />
            <p className={styles.text}>{description}</p>
        </Card>
    );
};
