import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import palacesData from '../data/palaces.json';
import './MemoryPage.css';

const MemoryPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [palace, setPalace] = useState(null);

  useEffect(() => {
    const palaceName = decodeURIComponent(location.pathname.split('/')[2]);
    const foundPalace = palacesData.palaces.find(p => p.name === palaceName);
    setPalace(foundPalace);
  }, [location]);

  const renderLines = (lines) => {
    return lines.map((line, index) => (
      <div key={index} className={`line ${line === 1 ? 'yang' : 'yin'}`}>
        {line === 1 ? '—' : '- -'}
        {line === 0 && <span className="vertical-line">│</span>}
      </div>
    ));
  };

  const handleStartTest = () => {
    navigate(`/test/${encodeURIComponent(palace.name)}`, { state: { palaceData: palace } });
  };

  if (!palace) return <div>Loading...</div>;

  return (
    <div className="memory-page-container">
      <h1 className="palace-name">{palace.name}</h1>
      <div className="hexagrams-container">
        {palace.hexagrams.map((hexagram, index) => (
          <div key={index} className="hexagram-card">
            <h2 className="hexagram-name">{hexagram.name}</h2>
            <div className="lines-container">{renderLines(hexagram.lines)}</div>
          </div>
        ))}
      </div>
      <button className="start-test-btn" onClick={handleStartTest}>开始测试</button>
    </div>
  );
};

export default MemoryPage;