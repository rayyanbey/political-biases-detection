import React from "react";

export function ErrorDisplay({ error, onRetry }) {
  return (
    <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6 mb-6">
      <div className="flex gap-4">
        <div className="text-red-600 text-2xl flex-shrink-0">🚨</div>
        <div className="flex-grow">
          <h3 className="font-bold text-red-800 mb-2">Analysis Failed</h3>
          <p className="text-red-700 text-sm mb-4">{error}</p>
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}

export default ErrorDisplay;
