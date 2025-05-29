import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import palacesData from '../data/palaces.json';
import './PalaceList.css';

const PalaceList = () => {
  const [palaces, setPalaces] = useState([]);

  useEffect(() => {
    setPalaces(palacesData.palaces);
  }, []);

  const renderLines = (lines) => {
    return lines.map((line, index) => (
      <div key={index} className={`line ${line === 1 ? 'yang' : 'yin'}`}>
        {line === 1 ? '—' : '- -'}
        {line === 0 && <span className="vertical-line">│</span>}
      </div>
    ));
  };

  return (
    <div className="palace-list-container">
      <div className="palace-grid">
        {palaces.map((palace) => (
          <Link 
            key={palace.name} 
            to={`/memory/${encodeURIComponent(palace.name)}`} 
            state={{ palaceData: palace }} 
            className="palace-card"
          >
            <h2 className="palace-title">{palace.name}</h2>
            <div className="lines-container">{renderLines(palace.hexagrams[0].lines)}</div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default PalaceList;