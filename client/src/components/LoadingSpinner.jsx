import React from "react";

export function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-4 border-gray-200"></div>
        <div
          className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-blue-600 border-r-blue-600 animate-spin"
          style={{ animation: "spin 1s linear infinite" }}
        ></div>
      </div>
      <p className="mt-6 text-lg font-medium text-gray-700">Analyzing...</p>
      <p className="mt-2 text-sm text-gray-500">
        This typically takes 3-5 seconds
      </p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default LoadingSpinner;
