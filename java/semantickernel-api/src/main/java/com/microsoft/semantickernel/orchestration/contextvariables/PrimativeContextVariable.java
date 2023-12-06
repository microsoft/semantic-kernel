// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatHistory.Message;
import com.microsoft.semantickernel.orchestration.ContextVariable;
import java.util.Iterator;
import java.util.Spliterator;
import java.util.function.Consumer;

public class PrimativeContextVariable {

    public static class NumberVariable<T extends Number> extends ContextVariable<T> {

        public NumberVariable(T value) {
            super(value);
        }

        public static NumberVariable of(Number n) {
            return new NumberVariable<>(n);
        }

        @Override
        public String toPromptString() {
            return getValue().toString();
        }

        @Override
        public NumberVariable<T> append(ContextVariable content) {
            return null;
        }

        @Override
        public NumberVariable<T> cloneVariable() {
            return new NumberVariable<>(getValue());
        }
    }

    public static class BooleanVariable extends ContextVariable<Boolean> {

        public BooleanVariable(Boolean value) {
            super(value);
        }

        public static BooleanVariable of(boolean b) {
            return new BooleanVariable(b);
        }

        @Override
        public String toPromptString() {
            return getValue().toString();
        }

        @Override
        public BooleanVariable append(ContextVariable content) {
            return null;
        }

        @Override
        public BooleanVariable cloneVariable() {
            return new BooleanVariable(getValue());
        }
    }

    public static class CharacterVariable extends ContextVariable<Character> {

        public CharacterVariable(Character value) {
            super(value);
        }

        @Override
        public String toPromptString() {
            return getValue().toString();
        }

        @Override
        public CharacterVariable append(ContextVariable content) {
            return null;
        }

        @Override
        public CharacterVariable cloneVariable() {
            return new CharacterVariable(getValue());
        }
    }

    public static class StringVariable extends ContextVariable<String> {

        public StringVariable(String value) {
            super(value);
        }

        public static StringVariable of(String s) {
            return new StringVariable(s);
        }

        @Override
        public String toPromptString() {
            return getValue().toString();
        }

        @Override
        public StringVariable append(ContextVariable content) {
            return StringVariable.of(getValue() + content.getValue());
        }

        @Override
        public ContextVariable<String> cloneVariable() {
            return new StringVariable(getValue());
        }
    }

    public static class ChatHistoryVariable extends ContextVariable<ChatHistory> implements Iterable<ChatHistory.Message> {

        public ChatHistoryVariable(ChatHistory value) {
            super(new ChatHistory(value.getMessages()));
        }

        public static ChatHistoryVariable of(ChatHistory s) {
            return new ChatHistoryVariable(s);
        }

        @Override
        public String toPromptString() {
            return getValue().toString();
        }

        @Override
        public ContextVariable<ChatHistory> append(ContextVariable content) {
            getValue().addAll((ChatHistory) content.getValue());
            return this;
        }

        @Override
        public ContextVariable<ChatHistory> cloneVariable() {
            return new ChatHistoryVariable(getValue());
        }

        @Override
        public Iterator<Message> iterator() {
            return getValue().getMessages().iterator();
        }

        @Override
        public void forEach(Consumer<? super Message> action) {
            getValue().getMessages().forEach(action);
        }

        @Override
        public Spliterator<Message> spliterator() {
            return getValue().getMessages().spliterator();
        }
    }
}
