import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Typography, 
  Spin, 
  Alert, 
  Tag,
  Space
} from 'antd';
import { 
  SearchOutlined, 
  DatabaseOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { searchLogService } from '../services/api';

const { Title, Text } = Typography;

const SearchHistory = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSearchLogs();
  }, []);

  const loadSearchLogs = async () => {
    try {
      setLoading(true);
      const data = await searchLogService.getSearchLogs();
      setLogs(data);
    } catch (err) {
      setError('Ошибка при загрузке истории поисков');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Тип поиска',
      dataIndex: 'search_type',
      key: 'search_type',
      render: (type) => (
        <Tag 
          color={type === 'company' ? 'blue' : 'green'}
          icon={type === 'company' ? <SearchOutlined /> : <DatabaseOutlined />}
        >
          {type === 'company' ? 'Поиск компании' : 'Поиск по оборудованию'}
        </Tag>
      ),
    },
    {
      title: 'Запрос',
      dataIndex: 'query',
      key: 'query',
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: 'Результатов найдено',
      dataIndex: 'results_count',
      key: 'results_count',
      render: (count) => (
        <Tag color={count > 0 ? 'green' : 'red'}>
          {count}
        </Tag>
      ),
    },
    {
      title: 'Дата и время',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => (
        <Space>
          <ClockCircleOutlined />
          <Text>{new Date(date).toLocaleString('ru-RU')}</Text>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Загрузка истории поисков...</Text>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>История поисков</Title>
      <Text type="secondary">
        Все выполненные поиски через систему AGB Searcher
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
          dataSource={logs}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} из ${total} записей`,
          }}
        />
      </Card>
    </div>
  );
};

export default SearchHistory;
