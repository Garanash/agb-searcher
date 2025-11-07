import React, { useState } from 'react';
import { 
  Form, 
  Input, 
  Button, 
  Card, 
  Typography, 
  Spin, 
  Alert, 
  Space,
  Divider,
  Tag,
  message
} from 'antd';
import { SearchOutlined, GlobalOutlined, MailOutlined, PhoneOutlined, EnvironmentOutlined, PlusOutlined, DatabaseOutlined } from '@ant-design/icons';
import { companyService } from '../services/api';

const { Title, Text } = Typography;

const CompanySearch = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const handleSearch = async (values) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await companyService.searchCompany(values.companyName);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Произошла ошибка при поиске');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToDatabase = async () => {
    if (!result) return;

    setSaving(true);
    try {
      const companyData = {
        name: result.name,
        website: result.website || "",
        email: result.email || "",
        address: result.address || "",
        phone: result.phone || "",
        description: result.description || "",
        equipment_purchased: result.equipment || ""
      };

      await companyService.createCompany(companyData);
      message.success('Компания успешно добавлена в базу данных!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Произошла ошибка при добавлении компании';
      message.error(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Title level={2}>Поиск информации о компании</Title>
      <Text type="secondary">
        Введите название компании для поиска контактной информации через Polza.AI
      </Text>

      <Card className="search-form">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSearch}
        >
          <Form.Item
            name="companyName"
            label="Название компании"
            rules={[
              { required: true, message: 'Пожалуйста, введите название компании' }
            ]}
          >
            <Input 
              placeholder="Например: ООО Рога и Копыта" 
              size="large"
              prefix={<SearchOutlined />}
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              size="large"
              icon={<SearchOutlined />}
            >
              Найти информацию
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {loading && (
        <div className="loading-container">
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>Поиск информации о компании...</Text>
          </div>
        </div>
      )}

      {error && (
        <Alert
          message="Ошибка поиска"
          description={error}
          type="error"
          showIcon
          className="error-message"
        />
      )}

      {result && (
        <Card 
          title={`Информация о компании: ${result.name}`} 
          className="results-container"
          extra={
            <Button 
              type="primary" 
              icon={<DatabaseOutlined />}
              onClick={handleAddToDatabase}
              loading={saving}
            >
              Добавить в базу компаний
            </Button>
          }
        >
          {!result.website && !result.email && !result.phone && !result.address && !result.description && !result.equipment ? (
            <Alert
              message="Информация не найдена"
              description="К сожалению, не удалось найти информацию о данной компании. Попробуйте уточнить название компании или проверить правильность написания."
              type="warning"
              showIcon
            />
          ) : (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {result.website && (
                <div className="company-info">
                  <GlobalOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  <strong>Сайт:</strong> 
                  <a href={result.website} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8 }}>
                    {result.website}
                  </a>
                </div>
              )}

              {result.email && (
                <div className="company-info">
                  <MailOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  <strong>Email:</strong> 
                  <a href={`mailto:${result.email}`} style={{ marginLeft: 8 }}>
                    {result.email}
                  </a>
                </div>
              )}

              {result.phone && (
                <div className="company-info">
                  <PhoneOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  <strong>Телефон:</strong> 
                  <span style={{ marginLeft: 8 }}>{result.phone}</span>
                </div>
              )}

              {result.address && (
                <div className="company-info">
                  <EnvironmentOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                  <strong>Адрес:</strong> 
                  <span style={{ marginLeft: 8 }}>{result.address}</span>
                </div>
              )}

              {result.equipment && (
                <div className="company-info">
                  <strong>Оборудование:</strong> 
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {result.equipment}
                  </Tag>
                </div>
              )}

              {result.description && (
                <>
                  <Divider />
                  <div>
                    <strong>Описание:</strong>
                    <div style={{ marginTop: 8 }}>
                      <Text>{result.description}</Text>
                    </div>
                  </div>
                </>
              )}
            </Space>
          )}
        </Card>
      )}
    </div>
  );
};

export default CompanySearch;
