import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Button, 
  Typography, 
  Space, 
  Divider, 
  Upload, 
  List, 
  message, 
  Modal, 
  Tabs, 
  Row, 
  Col,
  Tag,
  Popconfirm,
  Drawer
} from 'antd';
import { 
  SettingOutlined, 
  UploadOutlined, 
  DeleteOutlined, 
  PlusOutlined, 
  RobotOutlined,
  FileTextOutlined,
  SaveOutlined
} from '@ant-design/icons';
import { dialogService, settingsService } from '../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

const DialogSettings = () => {
  const [form] = Form.useForm();
  const [assistantForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [dialogs, setDialogs] = useState([]);
  const [selectedDialog, setSelectedDialog] = useState(null);
  const [settings, setSettings] = useState(null);
  const [files, setFiles] = useState([]);
  const [assistants, setAssistants] = useState([]);
  const [models, setModels] = useState([]);
  const [showAssistantModal, setShowAssistantModal] = useState(false);
  const [showSettingsDrawer, setShowSettingsDrawer] = useState(false);

  useEffect(() => {
    loadDialogs();
    loadAssistants();
    loadModels();
  }, []);

  const loadDialogs = async () => {
    try {
      const dialogsData = await dialogService.getDialogs();
      setDialogs(dialogsData);
    } catch (error) {
      console.error('Ошибка при загрузке диалогов:', error);
      message.error('Ошибка при загрузке диалогов');
    }
  };

  const loadAssistants = async () => {
    try {
      const assistantsData = await settingsService.getAssistants();
      setAssistants(assistantsData);
    } catch (error) {
      console.error('Ошибка при загрузке помощников:', error);
    }
  };

  const loadModels = async () => {
    try {
      const modelsData = await settingsService.getModels();
      setModels(modelsData);
    } catch (error) {
      console.error('Ошибка при загрузке моделей:', error);
    }
  };

  const loadDialogSettings = async (dialogId) => {
    try {
      const settingsData = await settingsService.getDialogSettings(dialogId);
      setSettings(settingsData);
      form.setFieldsValue(settingsData);
    } catch (error) {
      console.error('Ошибка при загрузке настроек:', error);
      // Если настроек нет, создаем пустые
      setSettings(null);
      form.resetFields();
    }
  };

  const loadDialogFiles = async (dialogId) => {
    try {
      const filesData = await settingsService.getDialogFiles(dialogId);
      setFiles(filesData);
    } catch (error) {
      console.error('Ошибка при загрузке файлов:', error);
      setFiles([]);
    }
  };

  const handleDialogSelect = (dialogId) => {
    const dialog = dialogs.find(d => d.id === dialogId);
    setSelectedDialog(dialog);
    loadDialogSettings(dialogId);
    loadDialogFiles(dialogId);
    setShowSettingsDrawer(true);
  };

  const handleSaveSettings = async (values) => {
    if (!selectedDialog) return;

    setLoading(true);
    try {
      if (settings) {
        await settingsService.updateDialogSettings(selectedDialog.id, values);
        message.success('Настройки обновлены');
      } else {
        await settingsService.createDialogSettings(selectedDialog.id, values);
        message.success('Настройки созданы');
      }
      loadDialogSettings(selectedDialog.id);
    } catch (error) {
      console.error('Ошибка при сохранении настроек:', error);
      message.error('Ошибка при сохранении настроек');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!selectedDialog) return;

    try {
      const formData = new FormData();
      formData.append('file', file);
      await settingsService.uploadDialogFile(selectedDialog.id, formData);
      message.success('Файл загружен');
      loadDialogFiles(selectedDialog.id);
    } catch (error) {
      console.error('Ошибка при загрузке файла:', error);
      message.error('Ошибка при загрузке файла');
    }
    return false; // Предотвращаем автоматическую загрузку
  };

  const handleDeleteFile = async (fileId) => {
    if (!selectedDialog) return;

    try {
      await settingsService.deleteDialogFile(selectedDialog.id, fileId);
      message.success('Файл удален');
      loadDialogFiles(selectedDialog.id);
    } catch (error) {
      console.error('Ошибка при удалении файла:', error);
      message.error('Ошибка при удалении файла');
    }
  };

  const handleCreateAssistant = async (values) => {
    setLoading(true);
    try {
      await settingsService.createAssistant(values);
      message.success('Помощник создан');
      setShowAssistantModal(false);
      assistantForm.resetFields();
      loadAssistants();
    } catch (error) {
      console.error('Ошибка при создании помощника:', error);
      message.error('Ошибка при создании помощника');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAssistant = async (assistantId) => {
    try {
      await settingsService.deleteAssistant(assistantId);
      message.success('Помощник удален');
      loadAssistants();
    } catch (error) {
      console.error('Ошибка при удалении помощника:', error);
      message.error('Ошибка при удалении помощника');
    }
  };

  const handleApplyAssistant = async (assistant) => {
    if (!selectedDialog) return;

    const settings = {
      system_prompt: assistant.system_prompt,
      model: assistant.model,
      temperature: assistant.temperature,
      max_tokens: assistant.max_tokens
    };

    setLoading(true);
    try {
      if (settings) {
        await settingsService.updateDialogSettings(selectedDialog.id, settings);
      } else {
        await settingsService.createDialogSettings(selectedDialog.id, settings);
      }
      message.success('Настройки помощника применены');
      loadDialogSettings(selectedDialog.id);
    } catch (error) {
      console.error('Ошибка при применении помощника:', error);
      message.error('Ошибка при применении помощника');
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined /> Настройки диалогов
        </Title>
        <Text type="secondary">
          Управляйте настройками диалогов, загружайте файлы и создавайте помощников
        </Text>
      </div>

      <Row gutter={[24, 24]}>
        {/* Список диалогов */}
        <Col xs={24} lg={8}>
          <Card title="Диалоги" extra={<Button icon={<PlusOutlined />} onClick={() => setShowSettingsDrawer(true)}>Настройки</Button>}>
            <List
              dataSource={dialogs}
              renderItem={(dialog) => (
                <List.Item
                  actions={[
                    <Button 
                      type="link" 
                      onClick={() => handleDialogSelect(dialog.id)}
                    >
                      Настроить
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    title={dialog.title}
                    description={
                      <div>
                        <div>{new Date(dialog.updated_at).toLocaleString('ru-RU')}</div>
                        <Tag color="blue">ID: {dialog.id}</Tag>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* Помощники */}
        <Col xs={24} lg={16}>
          <Card 
            title="Предустановленные помощники" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => setShowAssistantModal(true)}
              >
                Создать помощника
              </Button>
            }
          >
            <List
              dataSource={assistants}
              renderItem={(assistant) => (
                <List.Item
                  actions={[
                    <Button 
                      type="link" 
                      onClick={() => handleApplyAssistant(assistant)}
                      disabled={!selectedDialog}
                    >
                      Применить
                    </Button>,
                    <Popconfirm
                      title="Удалить помощника?"
                      onConfirm={() => handleDeleteAssistant(assistant.id)}
                    >
                      <Button type="link" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <div>
                        <RobotOutlined style={{ marginRight: 8 }} />
                        {assistant.name}
                        <Tag color="green" style={{ marginLeft: 8 }}>{assistant.model}</Tag>
                      </div>
                    }
                    description={
                      <div>
                        <div>{assistant.description}</div>
                        <div style={{ marginTop: 4 }}>
                          <Tag>Temperature: {assistant.temperature}</Tag>
                          <Tag>Max tokens: {assistant.max_tokens}</Tag>
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Drawer с настройками диалога */}
      <Drawer
        title={`Настройки диалога: ${selectedDialog?.title || ''}`}
        width={800}
        open={showSettingsDrawer}
        onClose={() => setShowSettingsDrawer(false)}
        extra={
          <Button 
            type="primary" 
            icon={<SaveOutlined />}
            onClick={() => form.submit()}
            loading={loading}
          >
            Сохранить
          </Button>
        }
      >
        {selectedDialog && (
          <Tabs defaultActiveKey="settings">
            <TabPane tab="Настройки" key="settings">
              <Form
                form={form}
                layout="vertical"
                onFinish={handleSaveSettings}
              >
                <Form.Item
                  name="system_prompt"
                  label="Системный промпт"
                  tooltip="Инструкции для AI о том, как он должен себя вести в этом диалоге"
                >
                  <TextArea
                    rows={6}
                    placeholder="Введите системный промпт для этого диалога..."
                  />
                </Form.Item>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="model"
                      label="Модель"
                      tooltip="Выберите модель AI для этого диалога"
                    >
                      <Select placeholder="Выберите модель">
                        {models.map(model => (
                          <Option key={model.id} value={model.id}>
                            <div>
                              <div>{model.name}</div>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {model.description}
                              </Text>
                            </div>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="temperature"
                      label="Temperature"
                      tooltip="Креативность ответов (0.0 - точные, 1.0 - креативные)"
                    >
                      <Select placeholder="Выберите temperature">
                        <Option value="0.1">0.1 - Очень точные</Option>
                        <Option value="0.3">0.3 - Точные</Option>
                        <Option value="0.7">0.7 - Сбалансированные</Option>
                        <Option value="1.0">1.0 - Креативные</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item
                  name="max_tokens"
                  label="Максимум токенов"
                  tooltip="Максимальная длина ответа"
                >
                  <Input type="number" placeholder="1000" />
                </Form.Item>
              </Form>
            </TabPane>

            <TabPane tab="Файлы" key="files">
              <div style={{ marginBottom: 16 }}>
                <Upload
                  beforeUpload={handleFileUpload}
                  showUploadList={false}
                  accept=".txt,.pdf,.doc,.docx,.md"
                >
                  <Button icon={<UploadOutlined />}>
                    Загрузить файл
                  </Button>
                </Upload>
              </div>

              <List
                dataSource={files}
                renderItem={(file) => (
                  <List.Item
                    actions={[
                      <Popconfirm
                        title="Удалить файл?"
                        onConfirm={() => handleDeleteFile(file.id)}
                      >
                        <Button type="link" danger icon={<DeleteOutlined />} />
                      </Popconfirm>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<FileTextOutlined />}
                      title={file.filename}
                      description={
                        <div>
                          <div>Тип: {file.file_type}</div>
                          <div>Размер: {formatFileSize(file.file_size)}</div>
                          <div>Загружен: {new Date(file.created_at).toLocaleString('ru-RU')}</div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </TabPane>
          </Tabs>
        )}
      </Drawer>

      {/* Модальное окно создания помощника */}
      <Modal
        title="Создать помощника"
        open={showAssistantModal}
        onCancel={() => {
          setShowAssistantModal(false);
          assistantForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={assistantForm}
          layout="vertical"
          onFinish={handleCreateAssistant}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название помощника' }]}
          >
            <Input placeholder="Например: Аналитик данных" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Описание"
          >
            <TextArea rows={2} placeholder="Краткое описание помощника..." />
          </Form.Item>

          <Form.Item
            name="system_prompt"
            label="Системный промпт"
            rules={[{ required: true, message: 'Введите системный промпт' }]}
          >
            <TextArea 
              rows={6} 
              placeholder="Опишите, как должен себя вести этот помощник..."
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="model"
                label="Модель"
                rules={[{ required: true, message: 'Выберите модель' }]}
              >
                <Select placeholder="Выберите модель">
                  {models.map(model => (
                    <Option key={model.id} value={model.id}>
                      {model.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="temperature"
                label="Temperature"
              >
                <Select placeholder="Выберите temperature">
                  <Option value="0.1">0.1 - Очень точные</Option>
                  <Option value="0.3">0.3 - Точные</Option>
                  <Option value="0.7">0.7 - Сбалансированные</Option>
                  <Option value="1.0">1.0 - Креативные</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="max_tokens"
            label="Максимум токенов"
          >
            <Input type="number" placeholder="1000" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                Создать
              </Button>
              <Button onClick={() => setShowAssistantModal(false)}>
                Отмена
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DialogSettings;
