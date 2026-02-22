import React from 'react';

const PhonemeDisplay = ({ diffs }) => {
  if (!diffs || diffs.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 p-4 bg-white rounded-lg shadow-sm">
      {diffs.map((item, index) => {
        let bgColor = 'bg-gray-100';
        let borderColor = 'border-gray-200';
        let textColor = 'text-gray-800';

        if (item.status === 'match') {
          bgColor = 'bg-green-100';
          borderColor = 'border-green-300';
          textColor = 'text-green-800';
        } else if (item.status === 'substitution') {
          bgColor = 'bg-yellow-100';
          borderColor = 'border-yellow-300';
          textColor = 'text-yellow-800';
        } else if (item.status === 'missing') {
          bgColor = 'bg-red-100';
          borderColor = 'border-red-300';
          textColor = 'text-red-800';
        } else if (item.status === 'insertion') {
          bgColor = 'bg-blue-100';
          borderColor = 'border-blue-300';
          textColor = 'text-blue-800';
        }

        return (
          <div
            key={index}
            className={`flex flex-col items-center px-2 py-1 border rounded ${bgColor} ${borderColor}`}
            title={`Status: ${item.status}, User: ${item.user || '-'}`}
          >
            <span className={`text-lg font-bold ${textColor}`}>
              {item.phoneme || '_'}
            </span>
            {item.status !== 'match' && (
              <span className="text-xs text-gray-500">
                {item.user || '?'}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default PhonemeDisplay;
