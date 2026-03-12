import { Routes, Route } from 'react-router-dom'
import { ConfigProvider, App as AntApp, theme } from 'antd'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/Dashboard'
import Experiments from './pages/Experiments'
import ExperimentDetail from './pages/Experiments/Detail'
import TraceDetail from './pages/Experiments/TraceDetail'
import BadCases from './pages/BadCases'
import Products from './pages/Config/Products'
import Metrics from './pages/Config/Metrics'
import Datasets from './pages/Config/Datasets'
import Changelog from './pages/Changelog'

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#60a5fa',
          colorBgBase: '#0f172a',
          colorBgContainer: '#1e293b',
          borderRadius: 8,
        },
        components: {
          Menu: {
            darkItemBg: '#0f172a',
            darkSubMenuItemBg: '#0f172a',
            darkItemSelectedBg: 'rgba(96, 165, 250, 0.15)',
            darkItemSelectedColor: '#60a5fa',
            darkItemColor: '#475569',
            darkItemHoverColor: '#60a5fa',
            darkItemHoverBg: 'rgba(96, 165, 250, 0.1)',
          },
        },
      }}
    >
      <AntApp>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="experiments" element={<Experiments />} />
            <Route path="experiments/:id" element={<ExperimentDetail />} />
            <Route path="experiments/:id/traces/:traceId" element={<TraceDetail />} />
            <Route path="badcases" element={<BadCases />} />
            <Route path="config/products" element={<Products />} />
            <Route path="config/metrics" element={<Metrics />} />
            <Route path="config/datasets" element={<Datasets />} />
            <Route path="changelog" element={<Changelog />} />
          </Route>
        </Routes>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
