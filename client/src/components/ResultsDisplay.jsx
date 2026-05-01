import React, { useState } from "react";

export function ResultsDisplay({ results }) {
  const [copied, setCopied] = useState(null);

  if (!results) {
    return null;
  }

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopied(field);
    setTimeout(() => setCopied(null), 2000);
  };

  // Determine bias color
  const getBiasColor = (biasLevel) => {
    const colors = {
      NONE: "bg-green-50 border-green-200 text-green-800",
      LOW: "bg-yellow-50 border-yellow-200 text-yellow-800",
      MEDIUM: "bg-orange-50 border-orange-200 text-orange-800",
      HIGH: "bg-red-50 border-red-200 text-red-800",
    };
    return colors[biasLevel] || "bg-gray-50 border-gray-200 text-gray-800";
  };

  // Determine bias badge color
  const getBiasBadgeColor = (biasLevel) => {
    const colors = {
      NONE: "bg-green-100 text-green-800",
      LOW: "bg-yellow-100 text-yellow-800",
      MEDIUM: "bg-orange-100 text-orange-800",
      HIGH: "bg-red-100 text-red-800",
    };
    return colors[biasLevel] || "bg-gray-100 text-gray-800";
  };

  // Determine tone color
  const getToneColor = (tone) => {
    return tone === "POSITIVE"
      ? "bg-green-50 border-green-200 text-green-800"
      : "bg-red-50 border-red-200 text-red-800";
  };

  const getToneBadgeColor = (tone) => {
    return tone === "POSITIVE"
      ? "bg-green-100 text-green-800"
      : "bg-red-100 text-red-800";
  };

  return (
    <div className="space-y-6">
      {/* Truncation warning banner */}
      {results.truncation_warning && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded">
          <div className="flex gap-3">
            <div className="text-amber-600 text-lg font-bold">⚠️</div>
            <div className="text-amber-800 text-sm whitespace-pre-wrap">
              {results.truncation_warning}
            </div>
          </div>
        </div>
      )}

      {/* Results grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Tone Card */}
        <div
          className={`border-2 rounded-lg p-6 ${getToneColor(results.tone)}`}
        >
          <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
            😊 Tone
            <span
              className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${getToneBadgeColor(
                results.tone
              )}`}
            >
              {results.tone}
            </span>
          </h3>

          <div className="space-y-3 mb-4">
            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Confidence</p>
              <p className="text-sm font-medium capitalize">
                {results.tone_confidence}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Score</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    results.tone === "POSITIVE" ? "bg-green-500" : "bg-red-500"
                  }`}
                  style={{ width: `${results.tone_score * 100}%` }}
                ></div>
              </div>
              <p className="text-xs font-medium mt-1 opacity-75">
                {(results.tone_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          <button
            onClick={() => copyToClipboard(`Tone: ${results.tone}`, "tone")}
            className="w-full py-2 px-3 bg-opacity-20 hover:bg-opacity-30 transition-all rounded text-xs font-semibold"
          >
            {copied === "tone" ? "✓ Copied" : "Copy Result"}
          </button>
        </div>

        {/* Bias Card */}
        <div
          className={`border-2 rounded-lg p-6 ${getBiasColor(results.bias)}`}
        >
          <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
            ⚖️ Bias
            <span
              className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${getBiasBadgeColor(
                results.bias
              )}`}
            >
              {results.bias}
            </span>
          </h3>

          <div className="space-y-3 mb-4">
            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Score</p>
              <div className="flex items-center gap-2">
                <div className="flex-grow bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      results.bias_score <= 1.5
                        ? "bg-green-500"
                        : results.bias_score <= 2.5
                        ? "bg-yellow-500"
                        : results.bias_score <= 3.5
                        ? "bg-orange-500"
                        : "bg-red-500"
                    }`}
                    style={{ width: `${(results.bias_score / 5) * 100}%` }}
                  ></div>
                </div>
                <p className="text-sm font-semibold">
                  {results.bias_score.toFixed(1)}/5
                </p>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Analysis</p>
              <p className="text-sm line-clamp-3">{results.bias_explanation}</p>
            </div>
          </div>

          <button
            onClick={() =>
              copyToClipboard(
                `Bias: ${results.bias}\n${results.bias_explanation}`,
                "bias"
              )
            }
            className="w-full py-2 px-3 bg-opacity-20 hover:bg-opacity-30 transition-all rounded text-xs font-semibold"
          >
            {copied === "bias" ? "✓ Copied" : "Copy Result"}
          </button>
        </div>

        {/* Summary Card */}
        <div className="border-2 border-purple-200 bg-purple-50 text-purple-800 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-3">📝 Summary</h3>

          <div className="mb-4">
            <p className="text-sm line-clamp-5 leading-relaxed">
              {results.summary}
            </p>
          </div>

          <button
            onClick={() => copyToClipboard(`Summary:\n${results.summary}`, "summary")}
            className="w-full py-2 px-3 bg-purple-200 hover:bg-purple-300 transition-all rounded text-xs font-semibold text-purple-900"
          >
            {copied === "summary" ? "✓ Copied" : "Copy Result"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ResultsDisplay;
