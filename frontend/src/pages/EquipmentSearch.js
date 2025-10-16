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
  List,
  Tag,
  Divider
} from 'antd';
import { 
  SearchOutlined, 
  GlobalOutlined, 
  MailOutlined, 
  PhoneOutlined, 
  EnvironmentOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { equipmentService } from '../services/api';

const { Title, Text } = Typography;

const EquipmentSearch = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (values) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await equipmentService.searchCompaniesByEquipment(values.equipmentName);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Произошла ошибка при поиске');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={2}>Поиск компаний по оборудованию</Title>
      <Text type="secondary">
        Введите название оборудования для поиска компаний, которые его используют
      </Text>

      <Card className="search-form">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSearch}
        >
          <Form.Item
            name="equipmentName"
            label="Название оборудования"
            rules={[
              { required: true, message: 'Пожалуйста, введите название оборудования' }
            ]}
          >
            <Input 
              placeholder="Например: станок ЧПУ, промышленный робот" 
              size="large"
              prefix={<DatabaseOutlined />}
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
              Найти компании
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {loading && (
        <div className="loading-container">
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>Поиск компаний...</Text>
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
          title={`Компании, использующие: ${result.equipment_name}`}
          extra={<Tag color="green">Найдено: {result.total_found}</Tag>}
          className="results-container"
        >
          <List
            dataSource={result.companies}
            renderItem={(company, index) => (
              <List.Item key={index}>
                <Card size="small" style={{ width: '100%' }}>
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <Title level={4} style={{ margin: 0 }}>
                      {company.name}
                    </Title>
                    
                    <Space wrap>
                      {company.website && (
                        <Space>
                          <GlobalOutlined style={{ color: '#1890ff' }} />
                          <a href={company.website} target="_blank" rel="noopener noreferrer">
                            Сайт
                          </a>
                        </Space>
                      )}
                      
                      {company.email && (
                        <Space>
                          <MailOutlined style={{ color: '#1890ff' }} />
                          <a href={`mailto:${company.email}`}>
                            {company.email}
                          </a>
                        </Space>
                      )}
                      
                      {company.phone && (
                        <Space>
                          <PhoneOutlined style={{ color: '#1890ff' }} />
                          <span>{company.phone}</span>
                        </Space>
                      )}
                      
                      {company.address && (
                        <Space>
                          <EnvironmentOutlined style={{ color: '#1890ff' }} />
                          <span>{company.address}</span>
                        </Space>
                      )}
                    </Space>

                    {company.description && (
                      <>
                        <Divider style={{ margin: '8px 0' }} />
                        <Text type="secondary">{company.description}</Text>
                      </>
                    )}
                  </Space>
                </Card>
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
};

export default EquipmentSearch;
