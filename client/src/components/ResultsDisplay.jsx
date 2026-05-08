import React, { useState } from "react";

export function ResultsDisplay({ results }) {
  const [copied, setCopied] = useState(null);

  if (!results) return null;

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopied(field);
    setTimeout(() => setCopied(null), 2000);
  };

  // ── Sentiment ──────────────────────────────────────────────────────────────
  const tone = results.sentiment?.label?.toUpperCase() ?? "NEUTRAL";
  const toneConfidence = Number(results.sentiment?.confidence) || 0;

  const getToneColor = (t) => {
    if (t === "POSITIVE") return "bg-green-50 border-green-200 text-green-800";
    if (t === "NEGATIVE") return "bg-red-50 border-red-200 text-red-800";
    return "bg-gray-50 border-gray-200 text-gray-700";
  };
  const getToneBadgeColor = (t) => {
    if (t === "POSITIVE") return "bg-green-100 text-green-800";
    if (t === "NEGATIVE") return "bg-red-100 text-red-800";
    return "bg-gray-100 text-gray-700";
  };

  // ── Bias / Stance ──────────────────────────────────────────────────────────
  const biasCategory = results.stance?.category ?? "UNKNOWN";
  const biasLabel = results.stance?.label ?? "Unknown";
  const biasConfidence = Number(results.stance?.confidence) || 0;

  const getBiasColor = (cat) => {
    const map = {
      LOW_BIAS:    "bg-green-50 border-green-200 text-green-800",
      MEDIUM_BIAS: "bg-orange-50 border-orange-200 text-orange-800",
      HIGH_BIAS:   "bg-red-50 border-red-200 text-red-800",
    };
    return map[cat] ?? "bg-gray-50 border-gray-200 text-gray-700";
  };
  const getBiasBadgeColor = (cat) => {
    const map = {
      LOW_BIAS:    "bg-green-100 text-green-800",
      MEDIUM_BIAS: "bg-orange-100 text-orange-800",
      HIGH_BIAS:   "bg-red-100 text-red-800",
    };
    return map[cat] ?? "bg-gray-100 text-gray-700";
  };

  // ── Summary ────────────────────────────────────────────────────────────────
  const summary = results.summary ?? "No summary available.";
  const judgeScore = results.judge?.score ?? null;
  const judgeExplanation = results.judge?.explanation ?? "";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* Tone Card */}
        <div className={`border-2 rounded-lg p-6 ${getToneColor(tone)}`}>
          <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
            😊 Tone
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${getToneBadgeColor(tone)}`}>
              {tone}
            </span>
          </h3>
          <div className="space-y-3 mb-4">
            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Confidence</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    tone === "POSITIVE" ? "bg-green-500"
                    : tone === "NEGATIVE" ? "bg-red-500"
                    : "bg-gray-500"
                  }`}
                  style={{ width: `${toneConfidence * 100}%` }}
                />
              </div>
              <p className="text-xs font-medium mt-1 opacity-75">
                {(toneConfidence * 100).toFixed(0)}%
              </p>
            </div>
          </div>
          <button
            onClick={() => copyToClipboard(`Tone: ${tone} (${(toneConfidence * 100).toFixed(0)}%)`, "tone")}
            className="w-full py-2 px-3 bg-opacity-20 hover:bg-opacity-30 transition-all rounded text-xs font-semibold"
          >
            {copied === "tone" ? "✓ Copied" : "Copy Result"}
          </button>
        </div>

        {/* Bias Card */}
        <div className={`border-2 rounded-lg p-6 ${getBiasColor(biasCategory)}`}>
          <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
            ⚖️ Bias
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${getBiasBadgeColor(biasCategory)}`}>
              {biasCategory.replace("_", " ")}
            </span>
          </h3>
          <div className="space-y-3 mb-4">
            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Confidence</p>
              <div className="flex items-center gap-2">
                <div className="flex-grow bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      biasCategory === "LOW_BIAS" ? "bg-green-500"
                      : biasCategory === "MEDIUM_BIAS" ? "bg-orange-500"
                      : "bg-red-500"
                    }`}
                    style={{ width: `${biasConfidence * 100}%` }}
                  />
                </div>
                <p className="text-sm font-semibold">{(biasConfidence * 100).toFixed(0)}%</p>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold opacity-75 mb-1">Stance</p>
              <p className="text-sm capitalize">{biasLabel}</p>
            </div>
          </div>
          <button
            onClick={() => copyToClipboard(`Bias: ${biasCategory}\nStance: ${biasLabel}`, "bias")}
            className="w-full py-2 px-3 bg-opacity-20 hover:bg-opacity-30 transition-all rounded text-xs font-semibold"
          >
            {copied === "bias" ? "✓ Copied" : "Copy Result"}
          </button>
        </div>

        {/* Summary Card */}
        <div className="border-2 border-purple-200 bg-purple-50 text-purple-800 rounded-lg p-6">
          <h3 className="text-lg font-bold mb-3">📝 Summary</h3>
          <p className="text-sm line-clamp-5 leading-relaxed mb-4">{summary}</p>
          <button
            onClick={() => copyToClipboard(`Summary:\n${summary}`, "summary")}
            className="w-full py-2 px-3 bg-purple-200 hover:bg-purple-300 transition-all rounded text-xs font-semibold text-purple-900"
          >
            {copied === "summary" ? "✓ Copied" : "Copy Result"}
          </button>
        </div>

      </div>

      {/* Judge Card */}
      {judgeScore !== null && (
        <div className="mt-6 border-2 rounded-lg p-6 bg-white">
          <h3 className="text-lg font-bold mb-3">🧑‍⚖️ Judge Evaluation</h3>
          <div className="mb-3">
            <p className="text-xs font-semibold opacity-75 mb-1">Score</p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full bg-indigo-600`}
                style={{ width: `${judgeScore}%` }}
              />
            </div>
            <p className="text-xs font-medium mt-1 opacity-75">{judgeScore}%</p>
          </div>
          <div className="mb-3">
            <p className="text-xs font-semibold opacity-75 mb-1">Explanation</p>
            <p className="text-sm leading-relaxed">{judgeExplanation}</p>
          </div>
          <button
            onClick={() => copyToClipboard(`Judge: ${judgeScore}% - ${judgeExplanation}`, "judge")}
            className="w-full py-2 px-3 bg-indigo-100 hover:bg-indigo-200 transition-all rounded text-xs font-semibold text-indigo-900"
          >
            {copied === "judge" ? "✓ Copied" : "Copy Judge Result"}
          </button>
        </div>
      )}
    </div>
  );
}

export default ResultsDisplay;