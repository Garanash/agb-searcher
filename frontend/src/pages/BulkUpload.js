import React, { useState } from 'react';
import { 
  Upload, 
  Button, 
  Card, 
  Typography, 
  Alert, 
  Progress,
  Space,
  Divider
} from 'antd';
import { UploadOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons';
import { companyService } from '../services/api';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const BulkUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (file) => {
    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const data = await companyService.bulkSearchCompanies(file);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Произошла ошибка при загрузке файла');
    } finally {
      setUploading(false);
    }

    return false; // Предотвращаем автоматическую загрузку
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.xlsx,.xls,.csv',
    beforeUpload: handleUpload,
    showUploadList: false,
  };

  return (
    <div>
      <Title level={2}>Массовая загрузка компаний</Title>
      <Text type="secondary">
        Загрузите файл Excel или CSV со списком названий компаний для автоматического поиска информации
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>Требования к файлу:</Title>
            <ul>
              <li>Формат: Excel (.xlsx, .xls) или CSV</li>
              <li>Названия компаний должны быть в первом столбце</li>
              <li>Максимальный размер файла: 10 МБ</li>
              <li>Кодировка CSV: UTF-8</li>
            </ul>
          </div>

          <Divider />

          <Dragger {...uploadProps} disabled={uploading}>
            <p className="ant-upload-drag-icon">
              {uploading ? <FileExcelOutlined /> : <UploadOutlined />}
            </p>
            <p className="ant-upload-text">
              {uploading ? 'Обработка файла...' : 'Нажмите или перетащите файл сюда'}
            </p>
            <p className="ant-upload-hint">
              Поддерживаются файлы Excel и CSV
            </p>
          </Dragger>

          {uploading && (
            <div style={{ textAlign: 'center' }}>
              <Progress percent={50} status="active" />
              <div style={{ marginTop: 16 }}>
                <Text>Поиск информации о компаниях через Polza.AI...</Text>
              </div>
            </div>
          )}

          {error && (
            <Alert
              message="Ошибка загрузки"
              description={error}
              type="error"
              showIcon
            />
          )}

          {result && (
            <Alert
              message="Загрузка завершена"
              description={
                <div>
                  <p><strong>Обработано компаний:</strong> {result.companies_processed}</p>
                  <p><strong>Найдено информации:</strong> {result.companies_found}</p>
                  <p>{result.message}</p>
                </div>
              }
              type="success"
              showIcon
            />
          )}
        </Space>
      </Card>

      <Card style={{ marginTop: 24 }}>
        <Title level={4}>Пример структуры файла</Title>
        <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4 }}>
          <pre style={{ margin: 0 }}>
{`Название компании
ООО Рога и Копыта
ИП Иванов И.И.
ЗАО ТехноМаш
ООО ПромСтанки
АО МеталлСервис`}
          </pre>
        </div>
      </Card>
    </div>
  );
};

export default BulkUpload;
