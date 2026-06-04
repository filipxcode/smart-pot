import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'ai';
    timestamp: Date;
}

// Historia rozmowy dla backendu (stateless): klient ją trzyma i odsyła z każdym pytaniem.
// Osobna od `messages`, które renderują dymki w UI.
interface ChatTurn {
    role: 'user' | 'assistant';
    content: string;
}

export default function ChatScreen() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            text: 'Cześć! Jestem Twoim asystentem botanicznym AI. Zapytaj mnie o stan Twojej doniczki, harmonogram podlewania lub ogólną pielęgnację rośliny.',
            sender: 'ai',
            timestamp: new Date(),
        },
    ]);
    const [inputText, setInputText] = useState('');
    const [chatHistory, setChatHistory] = useState<ChatTurn[]>([]);
    const flatListRef = useRef<FlatList>(null);

    // Mutacja obsługująca wysyłanie zapytania do agenta AI na backendzie
    const queryMutation = useMutation({
        mutationFn: async (userQuery: string) => {
            const response = await apiClient.post('/query', {
                query: userQuery,
                history: chatHistory, // dotychczasowa historia rozmowy
            });
            return response.data; // Zwraca: { answer: string, sources: [...], history: ChatTurn[] }
        },
        onSuccess: (data) => {
            // Serwer zwraca pełną, zaktualizowaną historię (z tą turą) — nadpisujemy.
            setChatHistory(data.history ?? []);
            const botMessage: Message = {
                id: Math.random().toString(),
                text: data.answer,
                sender: 'ai',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, botMessage]);
        },
        onError: (error) => {
            console.error('Błąd komunikacji z AI:', error);
            const errorMessage: Message = {
                id: Math.random().toString(),
                text: 'Przepraszam, wystąpił problem z połączeniem z systemem AI. Spróbuj ponownie za chwilę.',
                sender: 'ai',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        },
    });

    const handleSendMessage = () => {
        if (!inputText.trim() || queryMutation.isPending) return;

        const userMessageText = inputText.trim();
        setInputText('');

        const userMessage: Message = {
            id: Math.random().toString(),
            text: userMessageText,
            sender: 'user',
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);

        queryMutation.mutate(userMessageText);
    };

    const renderMessageItem = ({ item }: { item: Message }) => {
        const isUser = item.sender === 'user';
        return (
            <View style={[styles.messageRow, isUser ? styles.rowUser : styles.rowAi]}>
                <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAi]}>
                    <Text style={[styles.messageText, isUser ? styles.textUser : styles.textAi]}>
                        {item.text}
                    </Text>
                    <Text style={[styles.timeText, isUser ? styles.timeUser : styles.timeAi]}>
                        {item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Text>
                </View>
            </View>
        );
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 110} // Dostosuj offset pod wysokość bottom-tab-baru
        >
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Asystent Botaniczny AI</Text>
                <Text style={styles.headerStatus}>Połączony z bazą wiedzy</Text>
            </View>

            <FlatList
                ref={flatListRef}
                data={messages}
                keyExtractor={(item) => item.id}
                renderItem={renderMessageItem}
                contentContainerStyle={styles.chatContent}
                onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
                onLayout={() => flatListRef.current?.scrollToEnd({ animated: true })}
            />

            {/* Wskaźnik pisania przez AI */}
            {queryMutation.isPending && (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="small" color="#27ae60" />
                    <Text style={styles.loadingText}>Asystent analizuje dane...</Text>
                </View>
            )}

            <View style={styles.inputContainer}>
                <TextInput
                    style={styles.input}
                    placeholder="Zapytaj o coś!"
                    value={inputText}
                    onChangeText={setInputText}
                    multiline
                    maxLength={1000}
                />
                <TouchableOpacity
                    style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
                    onPress={handleSendMessage}
                    disabled={!inputText.trim() || queryMutation.isPending}
                >
                    <Text style={styles.sendButtonText}>Wyślij</Text>
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f9f9f9' },
    header: { backgroundColor: '#fff', padding: 15, borderBottomWidth: 1, borderBottomColor: '#eee', alignItems: 'center', paddingTop: Platform.OS === 'ios' ? 20 : 15 },
    headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#2c3e50' },
    headerStatus: { fontSize: 12, color: '#27ae60', marginTop: 2 },
    chatContent: { padding: 15, paddingBottom: 20 },
    messageRow: { flexDirection: 'row', marginBottom: 15, width: '100%' },
    rowUser: { justifyContent: 'flex-end' },
    rowAi: { justifyContent: 'flex-start' },
    bubble: { maxWidth: '80%', borderRadius: 16, padding: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
    bubbleUser: { backgroundColor: '#27ae60', borderBottomRightRadius: 2 },
    bubbleAi: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#eee', borderBottomLeftRadius: 2 },
    messageText: { fontSize: 16, lineHeight: 22 },
    textUser: { color: '#fff' },
    textAi: { color: '#2c3e50' },
    timeText: { fontSize: 10, marginTop: 4, textAlign: 'right' },
    timeUser: { color: 'rgba(255,255,255,0.7)' },
    timeAi: { color: '#95a5a6' },
    loadingContainer: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingBottom: 10 },
    loadingText: { marginLeft: 8, color: '#7f8c8d', fontSize: 14, fontStyle: 'italic' },
    inputContainer: { flexDirection: 'row', padding: 10, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#eee', alignItems: 'center' },
    input: { flex: 1, backgroundColor: '#f5f7fa', borderWidth: 1, borderColor: '#e6ebf0', borderRadius: 20, paddingHorizontal: 15, paddingVertical: 8, paddingTop: 8, fontSize: 16, maxHeight: 100, marginRight: 10 },
    sendButton: { backgroundColor: '#27ae60', borderRadius: 20, paddingVertical: 10, paddingHorizontal: 20, justifyContent: 'center', alignItems: 'center' },
    sendButtonDisabled: { backgroundColor: '#bdc3c7' },
    sendButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 }
});