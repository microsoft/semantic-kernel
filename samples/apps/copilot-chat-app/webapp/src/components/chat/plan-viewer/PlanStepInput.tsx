import { Badge, Button, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { Checkmark16Regular, Dismiss16Regular, Edit16Regular } from '@fluentui/react-icons';
import { useCallback, useState } from 'react';
import { IPlanInput } from '../../../libs/models/Plan';

const useClasses = makeStyles({
    root: {
        ...shorthands.overflow('hidden'),
        display: 'flex',
    },
    buttons: {
        ...shorthands.padding(tokens.spacingVerticalNone),
        paddingLeft: tokens.spacingHorizontalXXS,
        minWidth: '18px',
    },
    input: {
        ...shorthands.margin(tokens.spacingHorizontalXXS),
        maxHeight: '10px',
        minHeight: '10px',
        fontSize: tokens.fontSizeBase200,
    },
    interactable: {
        zIndex: '50',
    },
});

interface PlanStepInputProps {
    input: IPlanInput;
    onEdit: (newValue: string) => void;
    enableEdits: boolean;
}

export const PlanStepInput: React.FC<PlanStepInputProps> = ({ input, onEdit, enableEdits }) => {
    const classes = useClasses();
    const [isEditingInput, setIsEditingInput] = useState(false);

    const [inputValue, setInputValue] = useState(input.Value);

    const onEditClick = useCallback(() => {
        setIsEditingInput(true);
    }, []);

    const onSubmitEdit = useCallback(() => {
        setIsEditingInput(false);
        onEdit(inputValue);
    }, [inputValue, onEdit]);

    const onCancel = useCallback(() => {
        setIsEditingInput(false);
        setInputValue(input.Value);
    }, [input.Value]);

    return (
        <Badge color="informative" shape="rounded" appearance="tint" className={classes.root}>
            {`${input.Key}: `}
            {!enableEdits && input.Value}
            {enableEdits && (
                <>
                    {isEditingInput ? (
                        <input
                            className={mergeClasses(classes.input, classes.interactable)}
                            style={{ width: input.Value.length * 6, minWidth: '75px' }}
                            placeholder={input.Value}
                            value={inputValue}
                            onChange={(event) => {
                                setInputValue(event.target.value);
                            }}
                            onKeyDown={(event) => {
                                if (event.key === 'Enter' && !event.shiftKey) {
                                    event.preventDefault();
                                    onSubmitEdit();
                                }
                            }}
                        />
                    ) : (
                        inputValue
                    )}
                    <Button
                        icon={isEditingInput ? <Checkmark16Regular /> : <Edit16Regular />}
                        appearance="transparent"
                        className={mergeClasses(classes.buttons, classes.interactable)}
                        onClick={isEditingInput ? onSubmitEdit : onEditClick}
                    />
                    {isEditingInput && (
                        <Button
                            icon={<Dismiss16Regular />}
                            appearance="transparent"
                            className={mergeClasses(classes.buttons, classes.interactable)}
                            onClick={onCancel}
                        />
                    )}
                </>
            )}
        </Badge>
    );
};
