import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import palacesData from '../data/palaces.json';
import './TestPage.css';

const TestPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [palace, setPalace] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);
  const [results, setResults] = useState([]);

  useEffect(() => {
    const palaceName = decodeURIComponent(location.pathname.split('/')[2]);
    const foundPalace = palacesData.palaces.find(p => p.name === palaceName);
    setPalace(foundPalace);
    
    const initialAnswers = foundPalace?.hexagrams.map(hexagram => ({
      name: '',
      lines: [...hexagram.lines]
    })) || [];
    setUserAnswers(initialAnswers);
  }, [location]);

  const handleLineToggle = (hexagramIndex, lineIndex) => {
    const newAnswers = [...userAnswers];
    newAnswers[hexagramIndex].lines[lineIndex] = 1 - newAnswers[hexagramIndex].lines[lineIndex];
    setUserAnswers(newAnswers);
  };

  const handleNameChange = (e, hexagramIndex) => {
    const newAnswers = [...userAnswers];
    newAnswers[hexagramIndex].name = e.target.value;
    setUserAnswers(newAnswers);
  };

  const handleSubmit = () => {
    const newResults = palace.hexagrams.map((hexagram, index) => {
      const isNameCorrect = userAnswers[index].name === hexagram.name;
      const isLinesCorrect = userAnswers[index].lines.every((line, i) => line === hexagram.lines[i]);
      return isNameCorrect && isLinesCorrect;
    });
    setResults(newResults);
  };

  const handleRetest = () => {
    const initialAnswers = palace.hexagrams.map(hexagram => ({
      name: '',
      lines: [...hexagram.lines]
    }));
    setUserAnswers(initialAnswers);
    setResults([]);
  };

  if (!palace) return <div>Loading...</div>;

  return (
    <div className="test-page-container">
      <h1 className="palace-name">{palace.name}</h1>
      <div className="hexagrams-container">
        {palace.hexagrams.map((hexagram, index) => (
          <div key={index} className="hexagram-test-card">
            <input
              type="text"
              placeholder="输入卦名"
              value={userAnswers[index]?.name || ''}
              onChange={(e) => handleNameChange(e, index)}
              className={`hexagram-name-input ${results[index] === false ? 'wrong' : ''}`}
            />
            <div className="lines-interaction-container">
              {hexagram.lines.map((_, lineIndex) => (
                <button
                  key={lineIndex}
                  className={`line-btn ${userAnswers[index].lines[lineIndex] === 1 ? 'yang' : 'yin'}`}
                  onClick={() => handleLineToggle(index, lineIndex)}
                >
                  {userAnswers[index].lines[lineIndex] === 1 ? '—' : '- -'}
                  {userAnswers[index].lines[lineIndex] === 0 && <span className="vertical-line">│</span>}
                </button>
              ))}
            </div>
            {results[index] !== undefined && (
              <div className="result-indicator">
                {results[index] ? '正确' : '错误'}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="test-buttons">
        <button className="submit-btn" onClick={handleSubmit}>提交</button>
        <button className="retest-btn" onClick={handleRetest}>重新测试</button>
      </div>
    </div>
  );
};

export default TestPage;