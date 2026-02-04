import { useState, useEffect } from 'react';

const PromptModal = ({ prompt, onClose }) => {
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Parse prompt into main and example sections
  const parsePrompt = () => {
    const text = prompt.prompt_text;
    if (text.includes('---EXAMPLE---')) {
      const [promptPart, examplePart] = text.split('---EXAMPLE---');
      return {
        prompt: promptPart.trim(),
        example: examplePart.trim()
      };
    }
    return {
      prompt: text,
      example: null
    };
  };

  const { prompt: promptOnly, example: exampleSection } = parsePrompt();

  const handleCopyPrompt = async () => {
    try {
      await navigator.clipboard.writeText(promptOnly);
      setCopiedPrompt(true);
      setTimeout(() => setCopiedPrompt(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleCopyAll = async () => {
    try {
      await navigator.clipboard.writeText(prompt.prompt_text);
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Parse hierarchical category
  const parseCategory = (category) => {
    if (category && category.includes(' > ')) {
      const [mainCat, subCat] = category.split(' > ');
      return { main: mainCat, sub: subCat };
    }
    return { main: null, sub: category };
  };

  const { main: mainCategory, sub: subCategory } = parseCategory(prompt.category);

  if (!prompt) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {prompt.title}
            </h2>
            <div className="flex flex-wrap gap-2 items-center">
              {mainCategory && (
                <span className="inline-block px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm font-medium">
                  {mainCategory}
                </span>
              )}
              <span className="inline-block px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                {subCategory}
              </span>
              {prompt.source && (
                <span className="text-sm text-gray-600">
                  📚 Source: {prompt.source}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
            title="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Prompt Text */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">Prompt</h3>
              <div className="flex gap-2">
                <button
                  onClick={handleCopyPrompt}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    copiedPrompt
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  {copiedPrompt ? '✓ Copied!' : '📋 Copy Prompt Only'}
                </button>
                {exampleSection && (
                  <button
                    onClick={handleCopyAll}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      copiedAll
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {copiedAll ? '✓ Copied!' : 'Copy All'}
                  </button>
                )}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 leading-relaxed">
                {promptOnly}
              </pre>
            </div>
          </div>

          {/* Example Output Section (if exists) */}
          {exampleSection && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900">📘 Example Output</h3>
                <span className="text-sm text-gray-500 bg-yellow-50 px-3 py-1 rounded-full border border-yellow-200">
                  For reference only
                </span>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <pre className="whitespace-pre-wrap font-mono text-sm text-blue-900 leading-relaxed">
                  {exampleSection}
                </pre>
              </div>
            </div>
          )}

          {/* Tags */}
          {prompt.tags && prompt.tags.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {prompt.tags.map((tag, index) => (
                  <span 
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <span className="text-sm text-gray-600">Views</span>
              <p className="text-lg font-semibold text-gray-900">
                👁️ {prompt.views}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Added</span>
              <p className="text-lg font-semibold text-gray-900">
                {new Date(prompt.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              💡 Tip: Use variables like {'{variable_name}'} in your prompts for reusability
            </p>
            <button
              onClick={onClose}
              className="btn-secondary"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptModal;
