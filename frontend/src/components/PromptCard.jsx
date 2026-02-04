import { useState } from 'react';

const PromptCard = ({ prompt, onClick }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    try {
      // Extract only the prompt part (before example)
      let textToCopy = prompt.prompt_text;
      if (textToCopy.includes('---EXAMPLE---')) {
        textToCopy = textToCopy.split('---EXAMPLE---')[0].trim();
      }
      
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const truncateText = (text, maxLength = 150) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
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

  return (
    <div 
      onClick={onClick}
      className="card hover:shadow-md transition-shadow cursor-pointer group"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors flex-1">
            {prompt.title}
          </h3>
          <button
            onClick={handleCopy}
            className={`ml-3 px-3 py-1 rounded-lg text-sm font-medium transition-all ${
              copied 
                ? 'bg-green-100 text-green-700' 
                : 'bg-gray-100 text-gray-700 hover:bg-primary-100 hover:text-primary-700'
            }`}
            title="Copy prompt to clipboard"
          >
            {copied ? '✓ Copied!' : '📋 Copy'}
          </button>
        </div>

        {/* Category Badges - Hierarchical */}
        <div className="mb-3 flex flex-wrap gap-2 items-center">
          {mainCategory && (
            <span className="inline-block px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs font-medium">
              {mainCategory}
            </span>
          )}
          <span className="inline-block px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
            {subCategory}
          </span>
        </div>

        {/* Prompt Preview */}
        <p className="text-gray-600 mb-4 text-sm leading-relaxed">
          {truncateText(prompt.prompt_text)}
        </p>

        {/* Tags */}
        {prompt.tags && prompt.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {prompt.tags.slice(0, 3).map((tag, index) => (
              <span 
                key={index}
                className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded"
              >
                #{tag}
              </span>
            ))}
            {prompt.tags.length > 3 && (
              <span className="text-xs px-2 py-1 text-gray-500">
                +{prompt.tags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
          <div className="flex items-center space-x-4">
            <span>👁️ {prompt.views} views</span>
            {prompt.source && (
              <span className="flex items-center">
                <span className="mr-1">📚</span>
                {prompt.source}
              </span>
            )}
          </div>
          <span>
            {new Date(prompt.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PromptCard;
