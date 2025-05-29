import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PalaceList from './pages/PalaceList';
import MemoryPage from './pages/MemoryPage';
import TestPage from './pages/TestPage';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Router>
    <Routes>
      <Route path="/" element={<PalaceList />} />
      <Route path="/memory/:palaceName" element={<MemoryPage />} />
      <Route path="/test/:palaceName" element={<TestPage />} />
    </Routes>
  </Router>
);

// 创建 pages 目录
// mkdir -p src/pages