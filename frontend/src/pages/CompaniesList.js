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
  Input
} from 'antd';
import { 
  EditOutlined, 
  GlobalOutlined, 
  MailOutlined, 
  PhoneOutlined, 
  EnvironmentOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { companyService } from '../services/api';

const { Title, Text } = Typography;

const CompaniesList = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingCompany, setEditingCompany] = useState(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
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
    } catch (err) {
      console.error('Ошибка при сохранении:', err);
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

  return (
    <div>
      <Title level={2}>База данных компаний</Title>
      <Text type="secondary">
        Список всех компаний, найденных через систему поиска
      </Text>

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
    </div>
  );
};

export default CompaniesList;
