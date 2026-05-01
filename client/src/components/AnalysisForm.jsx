import React, { useState, useCallback } from "react";

export function AnalysisForm({ onSubmit, isLoading }) {
  const [text, setText] = useState("");
  const MAX_CHARS = 5000;
  const WARNING_THRESHOLD = 0.9;

  const charCount = text.length;
  const charPercentage = charCount / MAX_CHARS;
  const isNearLimit = charPercentage >= WARNING_THRESHOLD;
  const isOverLimit = charCount > MAX_CHARS;

  const handleChange = useCallback((e) => {
    const newText = e.target.value;
    // Allow typing up to the limit
    if (newText.length <= MAX_CHARS) {
      setText(newText);
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedText = text.trim();
    if (trimmedText && !isOverLimit) {
      onSubmit(trimmedText);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        Paste Your Text
      </h2>

      <form onSubmit={handleSubmit}>
        <div className="relative">
          <textarea
            value={text}
            onChange={handleChange}
            placeholder="Paste political text here (max 5000 characters)..."
            disabled={isLoading}
            className={`w-full h-48 p-4 border-2 rounded-lg font-mono text-sm resize-none focus:outline-none transition-colors ${
              isLoading
                ? "bg-gray-100 cursor-not-allowed border-gray-300"
                : isOverLimit
                ? "border-red-500 bg-red-50"
                : isNearLimit
                ? "border-yellow-500 bg-yellow-50"
                : "border-gray-300 bg-white focus:border-blue-500"
            }`}
          />

          {/* Character count indicator */}
          <div className="absolute bottom-2 right-2 bg-white px-2 py-1 rounded text-xs font-semibold">
            <span
              className={
                isOverLimit
                  ? "text-red-600"
                  : isNearLimit
                  ? "text-yellow-600"
                  : "text-gray-600"
              }
            >
              {charCount} / {MAX_CHARS}
            </span>
          </div>
        </div>

        {/* Warning messages */}
        {isNearLimit && !isOverLimit && (
          <div className="mt-2 text-sm text-yellow-700 bg-yellow-50 p-2 rounded">
            ⚠️ Approaching character limit
          </div>
        )}

        {isOverLimit && (
          <div className="mt-2 text-sm text-red-700 bg-red-50 p-2 rounded">
            🚨 Text exceeds maximum length. Please remove{" "}
            <strong>{charCount - MAX_CHARS} characters</strong>.
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={isLoading || !text.trim() || isOverLimit}
          className={`mt-4 px-8 py-3 rounded-lg font-semibold text-white transition-all transform ${
            isLoading || !text.trim() || isOverLimit
              ? "bg-gray-400 cursor-not-allowed opacity-60"
              : "bg-blue-600 hover:bg-blue-700 active:scale-95 cursor-pointer"
          }`}
        >
          {isLoading ? "Analyzing..." : "Analyze Text"}
        </button>
      </form>
    </div>
  );
}

export default AnalysisForm;
