import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, List, Card, Typography, Space, Spin, message, Modal, Drawer, Badge, Select, Tag } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, PlusOutlined, HistoryOutlined, DeleteOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { chatService, dialogService, settingsService } from '../services/api';

const { TextArea } = Input;
const { Text, Title } = Typography;

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentDialogId, setCurrentDialogId] = useState(null);
  const [dialogs, setDialogs] = useState([]);
  const [dialogsLoading, setDialogsLoading] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [newDialogTitle, setNewDialogTitle] = useState('');
  const [showNewDialogModal, setShowNewDialogModal] = useState(false);
  const [assistants, setAssistants] = useState([]);
  const [selectedAssistant, setSelectedAssistant] = useState(null);
  const [assistantsLoading, setAssistantsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Загружаем диалоги и помощников при монтировании компонента
  useEffect(() => {
    loadDialogs();
    loadAssistants();
  }, []);

  const loadDialogs = async () => {
    setDialogsLoading(true);
    try {
      const dialogsData = await dialogService.getDialogs();
      setDialogs(dialogsData);
    } catch (error) {
      console.error('Ошибка при загрузке диалогов:', error);
      message.error('Ошибка при загрузке диалогов');
    } finally {
      setDialogsLoading(false);
    }
  };

  const loadAssistants = async () => {
    setAssistantsLoading(true);
    try {
      console.log('Загружаем помощников...');
      const assistantsData = await settingsService.getAssistants();
      console.log('Получены помощники:', assistantsData);
      setAssistants(assistantsData);
    } catch (error) {
      console.error('Ошибка при загрузке помощников:', error);
      message.error('Ошибка при загрузке помощников');
    } finally {
      setAssistantsLoading(false);
    }
  };

  const loadDialog = async (dialogId) => {
    try {
      const dialogData = await dialogService.getDialog(dialogId);
      setMessages(dialogData.messages || []);
      setCurrentDialogId(dialogId);
      setDrawerVisible(false);
    } catch (error) {
      console.error('Ошибка при загрузке диалога:', error);
      message.error('Ошибка при загрузке диалога');
    }
  };

  const createNewDialog = async () => {
    if (!newDialogTitle.trim()) {
      message.warning('Введите название диалога');
      return;
    }

    try {
      const newDialog = await dialogService.createDialog(newDialogTitle);
      setDialogs([newDialog, ...dialogs]);
      setCurrentDialogId(newDialog.id);
      setMessages([]);
      setNewDialogTitle('');
      setShowNewDialogModal(false);
      setDrawerVisible(false);
      message.success('Новый диалог создан');
    } catch (error) {
      console.error('Ошибка при создании диалога:', error);
      message.error('Ошибка при создании диалога');
    }
  };

  const deleteDialog = async (dialogId) => {
    try {
      await dialogService.deleteDialog(dialogId);
      setDialogs(dialogs.filter(d => d.id !== dialogId));
      if (currentDialogId === dialogId) {
        setCurrentDialogId(null);
        setMessages([]);
      }
      message.success('Диалог удален');
    } catch (error) {
      console.error('Ошибка при удалении диалога:', error);
      message.error('Ошибка при удалении диалога');
    }
  };

  const startNewDialog = () => {
    setCurrentDialogId(null);
    setMessages([]);
    setDrawerVisible(false);
  };

  const handleAssistantSelect = async (assistantId) => {
    if (!assistantId) {
      setSelectedAssistant(null);
      return;
    }

    const assistant = assistants.find(a => a.id === assistantId);
    if (!assistant) return;

    setSelectedAssistant(assistant);

    // Если есть активный диалог, применяем настройки помощника
    if (currentDialogId) {
      try {
        const settings = {
          system_prompt: assistant.system_prompt,
          model: assistant.model,
          temperature: assistant.temperature,
          max_tokens: assistant.max_tokens
        };

        await settingsService.updateDialogSettings(currentDialogId, settings);
        message.success(`Помощник "${assistant.name}" применен к диалогу`);
      } catch (error) {
        console.error('Ошибка при применении помощника:', error);
        message.error('Ошибка при применении настроек помощника');
      }
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await chatService.sendDialogMessage(inputMessage, currentDialogId, messages);
      setMessages(response.conversation_history);
      setCurrentDialogId(response.dialog_id);
      
      // Обновляем список диалогов, если это новый диалог
      if (!currentDialogId) {
        loadDialogs();
      }
    } catch (error) {
      console.error('Ошибка при отправке сообщения:', error);
      message.error('Ошибка при отправке сообщения. Попробуйте снова.');
      
      // Добавляем сообщение об ошибке
      const errorMessage = {
        role: 'assistant',
        content: 'Извините, произошла ошибка при обработке вашего сообщения.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <Title level={3}>
              <RobotOutlined /> Чат с AI помощником
            </Title>
            <Text type="secondary">
              Задавайте вопросы о компаниях, оборудовании или используйте функции поиска
            </Text>
          </div>
          <Space>
            <Button 
              icon={<PlusOutlined />} 
              onClick={() => setShowNewDialogModal(true)}
              type="primary"
            >
              Новый диалог
            </Button>
            <Button 
              icon={<HistoryOutlined />} 
              onClick={() => setDrawerVisible(true)}
            >
              История диалогов
            </Button>
          </Space>
        </div>
        
        {/* Селектор помощников */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Text strong>Помощник:</Text>
          <Select
            placeholder="Выберите помощника"
            style={{ minWidth: 200 }}
            value={selectedAssistant?.id}
            onChange={handleAssistantSelect}
            loading={assistantsLoading}
            allowClear
          >
            {assistants.map(assistant => (
              <Select.Option key={assistant.id} value={assistant.id}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <RobotOutlined />
                  <span>{assistant.name}</span>
                  <Tag color="blue" size="small">{assistant.model}</Tag>
                </div>
              </Select.Option>
            ))}
          </Select>
          {selectedAssistant && (
            <Tag color="green" icon={<RobotOutlined />}>
              {selectedAssistant.name}
            </Tag>
          )}
          <Text type="secondary">({assistants.length} помощников)</Text>
        </div>
      </div>

      <Card 
        style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          marginBottom: 16,
          overflow: 'hidden'
        }}
        bodyStyle={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          padding: 0
        }}
      >
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: 16,
          maxHeight: '500px'
        }}>
          {messages.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              color: '#999', 
              marginTop: 50 
            }}>
              <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>Начните диалог с AI помощником</div>
              <div style={{ fontSize: 12, marginTop: 8 }}>
                Попробуйте спросить: "Расскажи о компании Газпром" или "Найди компании, использующие станки"
              </div>
            </div>
          ) : (
            <List
              dataSource={messages}
              renderItem={(msg) => (
                <List.Item style={{ border: 'none', padding: '8px 0' }}>
                  <div style={{ 
                    width: '100%',
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                  }}>
                    <div style={{
                      maxWidth: '70%',
                      backgroundColor: msg.role === 'user' ? '#1890ff' : '#f5f5f5',
                      color: msg.role === 'user' ? 'white' : 'black',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      position: 'relative'
                    }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        marginBottom: 4 
                      }}>
                        {msg.role === 'user' ? (
                          <UserOutlined style={{ marginRight: 8 }} />
                        ) : (
                          <RobotOutlined style={{ marginRight: 8 }} />
                        )}
                        <Text 
                          style={{ 
                            color: msg.role === 'user' ? 'white' : '#666',
                            fontSize: 12 
                          }}
                        >
                          {msg.role === 'user' ? 'Вы' : 'AI'} • {formatTime(msg.timestamp)}
                        </Text>
                      </div>
                      <div style={{ whiteSpace: 'pre-wrap' }}>
                        {msg.role === 'assistant' ? (
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              // Стилизация для Markdown элементов
                              h1: ({children}) => <h1 style={{fontSize: '1.5em', fontWeight: 'bold', margin: '8px 0'}}>{children}</h1>,
                              h2: ({children}) => <h2 style={{fontSize: '1.3em', fontWeight: 'bold', margin: '6px 0'}}>{children}</h2>,
                              h3: ({children}) => <h3 style={{fontSize: '1.1em', fontWeight: 'bold', margin: '4px 0'}}>{children}</h3>,
                              p: ({children}) => <p style={{margin: '4px 0'}}>{children}</p>,
                              ul: ({children}) => <ul style={{margin: '4px 0', paddingLeft: '20px'}}>{children}</ul>,
                              ol: ({children}) => <ol style={{margin: '4px 0', paddingLeft: '20px'}}>{children}</ol>,
                              li: ({children}) => <li style={{margin: '2px 0'}}>{children}</li>,
                              code: ({children, className}) => {
                                const isInline = !className;
                                return isInline ? (
                                  <code style={{
                                    backgroundColor: '#f5f5f5',
                                    padding: '2px 4px',
                                    borderRadius: '3px',
                                    fontFamily: 'monospace',
                                    fontSize: '0.9em'
                                  }}>{children}</code>
                                ) : (
                                  <pre style={{
                                    backgroundColor: '#f5f5f5',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    margin: '4px 0'
                                  }}>
                                    <code>{children}</code>
                                  </pre>
                                );
                              },
                              blockquote: ({children}) => (
                                <blockquote style={{
                                  borderLeft: '4px solid #d9d9d9',
                                  paddingLeft: '12px',
                                  margin: '4px 0',
                                  fontStyle: 'italic',
                                  color: '#666'
                                }}>{children}</blockquote>
                              ),
                              strong: ({children}) => <strong style={{fontWeight: 'bold'}}>{children}</strong>,
                              em: ({children}) => <em style={{fontStyle: 'italic'}}>{children}</em>,
                              table: ({children}) => (
                                <table style={{
                                  borderCollapse: 'collapse',
                                  width: '100%',
                                  margin: '4px 0',
                                  border: '1px solid #d9d9d9'
                                }}>{children}</table>
                              ),
                              th: ({children}) => (
                                <th style={{
                                  border: '1px solid #d9d9d9',
                                  padding: '8px',
                                  backgroundColor: '#fafafa',
                                  fontWeight: 'bold'
                                }}>{children}</th>
                              ),
                              td: ({children}) => (
                                <td style={{
                                  border: '1px solid #d9d9d9',
                                  padding: '8px'
                                }}>{children}</td>
                              )
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        ) : (
                          msg.content
                        )}
                      </div>
                    </div>
                  </div>
                </List.Item>
              )}
            />
          )}
          {loading && (
            <div style={{ textAlign: 'center', padding: 16 }}>
              <Spin />
              <div style={{ marginTop: 8 }}>AI думает...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </Card>

      <div style={{ display: 'flex', gap: 8 }}>
        <TextArea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Введите ваше сообщение..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          style={{ flex: 1 }}
          disabled={loading}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSendMessage}
          loading={loading}
          disabled={!inputMessage.trim()}
        >
          Отправить
        </Button>
      </div>

      {/* Модальное окно для создания нового диалога */}
      <Modal
        title="Создать новый диалог"
        open={showNewDialogModal}
        onOk={createNewDialog}
        onCancel={() => {
          setShowNewDialogModal(false);
          setNewDialogTitle('');
        }}
        okText="Создать"
        cancelText="Отмена"
      >
        <Input
          placeholder="Введите название диалога"
          value={newDialogTitle}
          onChange={(e) => setNewDialogTitle(e.target.value)}
          onPressEnter={createNewDialog}
        />
      </Modal>

      {/* Drawer с историей диалогов */}
      <Drawer
        title="История диалогов"
        placement="right"
        width={400}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setShowNewDialogModal(true)}
          >
            Новый
          </Button>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <Button 
            block 
            onClick={startNewDialog}
            style={{ marginBottom: 16 }}
          >
            <PlusOutlined /> Начать новый диалог
          </Button>
        </div>

        <Spin spinning={dialogsLoading}>
          <List
            dataSource={dialogs}
            renderItem={(dialog) => (
              <List.Item
                actions={[
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    onClick={() => deleteDialog(dialog.id)}
                    danger
                    size="small"
                  />
                ]}
              >
                <List.Item.Meta
                  title={
                    <div 
                      style={{ 
                        cursor: 'pointer',
                        color: currentDialogId === dialog.id ? '#1890ff' : 'inherit'
                      }}
                      onClick={() => loadDialog(dialog.id)}
                    >
                      {dialog.title}
                    </div>
                  }
                  description={
                    <div>
                      <div>{new Date(dialog.updated_at).toLocaleString('ru-RU')}</div>
                      {currentDialogId === dialog.id && (
                        <Badge status="processing" text="Активный диалог" />
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        </Spin>
      </Drawer>
    </div>
  );
};

export default Chat;
