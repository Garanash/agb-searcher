import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import { 
  SearchOutlined, 
  DatabaseOutlined, 
  HistoryOutlined,
  UploadOutlined,
  SettingOutlined 
} from '@ant-design/icons';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';

import CompanySearch from './pages/CompanySearch';
import EquipmentSearch from './pages/EquipmentSearch';
import CompaniesList from './pages/CompaniesList';
import BulkUpload from './pages/BulkUpload';
import SearchHistory from './pages/SearchHistory';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const AppLayout = () => {
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <SearchOutlined />,
      label: <Link to="/">Поиск компании</Link>,
    },
    {
      key: '/equipment',
      icon: <DatabaseOutlined />,
      label: <Link to="/equipment">Поиск по оборудованию</Link>,
    },
    {
      key: '/companies',
      icon: <DatabaseOutlined />,
      label: <Link to="/companies">База компаний</Link>,
    },
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: <Link to="/upload">Массовая загрузка</Link>,
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: <Link to="/history">История поисков</Link>,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={250} style={{ background: '#fff' }}>
        <div style={{ padding: '16px', textAlign: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
            AGB Searcher
          </Title>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Title level={3} style={{ margin: 0, lineHeight: '64px' }}>
            Система поиска информации о компаниях
          </Title>
        </Header>
        <Content style={{ margin: '24px', background: '#fff', borderRadius: '8px' }}>
          <Routes>
            <Route path="/" element={<CompanySearch />} />
            <Route path="/equipment" element={<EquipmentSearch />} />
            <Route path="/companies" element={<CompaniesList />} />
            <Route path="/upload" element={<BulkUpload />} />
            <Route path="/history" element={<SearchHistory />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;
