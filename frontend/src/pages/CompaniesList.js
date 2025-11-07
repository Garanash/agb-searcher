import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Typography, 
  Spin, 
  Alert, 
  Space,
  Tag,
  Button,
  Modal,
  Form,
  Input,
  message,
  Popconfirm
} from 'antd';
import { 
  EditOutlined, 
  GlobalOutlined, 
  MailOutlined, 
  PhoneOutlined, 
  EnvironmentOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SendOutlined,
  CheckOutlined
} from '@ant-design/icons';
import { companyService, emailService } from '../services/api';

const { Title, Text } = Typography;

const CompaniesList = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingCompany, setEditingCompany] = useState(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [emailCampaignModalVisible, setEmailCampaignModalVisible] = useState(false);
  const [emailCampaignForm] = Form.useForm();
  const [selectedCompanyIds, setSelectedCompanyIds] = useState([]);
  const [verifyingEmails, setVerifyingEmails] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const data = await companyService.getCompanies();
      setCompanies(data);
    } catch (err) {
      setError('Ошибка при загрузке списка компаний');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (company) => {
    setEditingCompany(company);
    form.setFieldsValue(company);
    setEditModalVisible(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await companyService.updateCompany(editingCompany.id, values);
      setEditModalVisible(false);
      loadCompanies();
      message.success('Компания успешно обновлена');
    } catch (err) {
      console.error('Ошибка при сохранении:', err);
      message.error('Ошибка при сохранении компании');
    }
  };

  const handleVerifyEmail = async (email, companyId) => {
    try {
      const result = await emailService.verifyEmail(email, companyId);
      if (result.is_deliverable) {
        message.success(`Email ${email} валиден и доставляем`);
      } else {
        message.warning(`Email ${email} не доставляем: ${result.error_message || 'Неизвестная ошибка'}`);
      }
      loadCompanies();
    } catch (err) {
      message.error('Ошибка при проверке email');
    }
  };

  const handleBulkVerifyEmails = async () => {
    setVerifyingEmails(true);
    try {
      const result = await emailService.bulkVerifyEmails();
      message.success(result.message);
      loadCompanies();
    } catch (err) {
      message.error('Ошибка при массовой проверке email');
    } finally {
      setVerifyingEmails(false);
    }
  };

  const handleCreateEmailCampaign = async () => {
    try {
      const values = await emailCampaignForm.validateFields();
      const campaign = await emailService.createCampaign({
        subject: values.subject,
        body: values.body,
        company_ids: selectedCompanyIds.length > 0 ? selectedCompanyIds : null
      });
      message.success('Рассылка создана');
      setEmailCampaignModalVisible(false);
      emailCampaignForm.resetFields();
      setSelectedCompanyIds([]);
    } catch (err) {
      message.error('Ошибка при создании рассылки');
    }
  };

  const handleSendEmailCampaign = async (campaignId) => {
    try {
      const result = await emailService.sendCampaign(campaignId);
      message.success(result.message);
    } catch (err) {
      message.error('Ошибка при отправке рассылки');
    }
  };

  const columns = [
    {
      title: 'Название компании',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          {record.is_verified && (
            <Tag color="green" icon={<CheckCircleOutlined />}>
              Проверено
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Контактная информация',
      key: 'contacts',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {record.website && (
            <Space>
              <GlobalOutlined style={{ color: '#1890ff' }} />
              <a href={record.website} target="_blank" rel="noopener noreferrer">
                Сайт
              </a>
            </Space>
          )}
          {record.email && (
            <Space>
              <MailOutlined style={{ color: '#1890ff' }} />
              <a href={`mailto:${record.email}`}>
                {record.email}
              </a>
              <Button
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleVerifyEmail(record.email, record.id)}
                title="Проверить email"
              />
            </Space>
          )}
          {record.phone && (
            <Space>
              <PhoneOutlined style={{ color: '#1890ff' }} />
              <span>{record.phone}</span>
            </Space>
          )}
          {record.address && (
            <Space>
              <EnvironmentOutlined style={{ color: '#1890ff' }} />
              <span>{record.address}</span>
            </Space>
          )}
        </Space>
      ),
    },
    {
      title: 'Оборудование',
      dataIndex: 'equipment_purchased',
      key: 'equipment_purchased',
      render: (text) => text ? <Tag color="blue">{text}</Tag> : '-',
    },
    {
      title: 'Язык рассылки',
      dataIndex: 'preferred_language',
      key: 'preferred_language',
      render: (lang) => {
        const langMap = {
          'ru': '🇷🇺 Русский',
          'en': '🇬🇧 English',
          'de': '🇩🇪 Deutsch',
          'fr': '🇫🇷 Français',
          'es': '🇪🇸 Español',
          'zh': '🇨🇳 中文',
          'ja': '🇯🇵 日本語'
        };
        return lang ? <Tag color="green">{langMap[lang] || lang}</Tag> : <Tag>🇷🇺 Русский</Tag>;
      },
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record) => (
        <Button 
          type="primary" 
          icon={<EditOutlined />}
          onClick={() => handleEdit(record)}
        >
          Редактировать
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Загрузка списка компаний...</Text>
        </div>
      </div>
    );
  }

  const rowSelection = {
    selectedRowKeys: selectedCompanyIds,
    onChange: (selectedRowKeys) => {
      setSelectedCompanyIds(selectedRowKeys);
    },
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <Title level={2}>База данных компаний</Title>
          <Text type="secondary">
            Список всех компаний, найденных через систему поиска
          </Text>
        </div>
        <Space>
          <Button
            icon={<CheckOutlined />}
            onClick={handleBulkVerifyEmails}
            loading={verifyingEmails}
          >
            Проверить все email
          </Button>
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => setEmailCampaignModalVisible(true)}
          >
            Создать email рассылку
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          message="Ошибка"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={companies}
          rowKey="id"
          rowSelection={rowSelection}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} из ${total} компаний`,
          }}
        />
      </Card>

      <Modal
        title="Редактировать компанию"
        open={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="website" label="Сайт">
            <Input placeholder="https://example.com" />
          </Form.Item>
          <Form.Item name="email" label="Email">
            <Input placeholder="info@example.com" />
          </Form.Item>
          <Form.Item name="phone" label="Телефон">
            <Input placeholder="+7 (495) 123-45-67" />
          </Form.Item>
          <Form.Item name="address" label="Адрес">
            <Input.TextArea placeholder="г. Москва, ул. Примерная, д. 1" />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <Input.TextArea placeholder="Описание деятельности компании" />
          </Form.Item>
          <Form.Item name="equipment_purchased" label="Оборудование">
            <Input placeholder="Список оборудования" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно для создания email рассылки */}
      <Modal
        title="Создать email рассылку"
        open={emailCampaignModalVisible}
        onOk={handleCreateEmailCampaign}
        onCancel={() => {
          setEmailCampaignModalVisible(false);
          emailCampaignForm.resetFields();
          setSelectedCompanyIds([]);
        }}
        width={700}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={emailCampaignForm} layout="vertical">
          <Form.Item
            name="subject"
            label="Тема письма"
            rules={[{ required: true, message: 'Введите тему письма' }]}
          >
            <Input placeholder="Тема email рассылки" />
          </Form.Item>
          <Form.Item
            name="body"
            label="Текст письма"
            rules={[{ required: true, message: 'Введите текст письма' }]}
          >
            <Input.TextArea 
              rows={8}
              placeholder="Текст email рассылки"
            />
          </Form.Item>
          <Form.Item>
            <Text type="secondary">
              {selectedCompanyIds.length > 0 
                ? `Рассылка будет отправлена ${selectedCompanyIds.length} выбранным компаниям`
                : 'Рассылка будет отправлена всем компаниям с email адресами'}
            </Text>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CompaniesList;
