import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { promptsAPI } from '../utils/api';
import { useCategories } from '../hooks/usePrompts';

const AddPromptPage = () => {
  const navigate = useNavigate();
  const { categories } = useCategories();
  
  const [formData, setFormData] = useState({
    title: '',
    prompt_text: '',
    example_output: '',
    category: '',
    tags: '',
    source: ''
  });
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [categoryCounts, setCategoryCounts] = useState({});
  const [existingPrompts, setExistingPrompts] = useState([]);

  // Fetch existing prompts for duplicate checking
  useEffect(() => {
    const loadPrompts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/prompts?limit=500');
        const data = await response.json();
        setExistingPrompts(data);
        console.log('Loaded prompts for duplicate check:', data.length);
      } catch (err) {
        console.error('Failed to load prompts:', err);
      }
    };
    loadPrompts();
  }, []);

  // Fetch category counts
  useEffect(() => {
    const fetchCategoryCounts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/stats');
        const stats = await response.json();
        setCategoryCounts(stats.categories || {});
      } catch (err) {
        console.error('Error fetching category counts:', err);
      }
    };
    fetchCategoryCounts();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
  e.preventDefault();

  // Check for duplicate (title + category, case-insensitive)
  const isDuplicate = existingPrompts.some(p => 
    p.title.trim().toLowerCase() === formData.title.trim().toLowerCase() && 
    p.category.toLowerCase() === formData.category.toLowerCase()
      
  );
  //console.log('Duplicate check:', { isDuplicate, existingCount: existingPrompts.length });

  if (isDuplicate) {
    setError('A prompt with this title and category already exists. Please use a different title or category.');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }

  setSubmitting(true);
  setError('');

  try {
    // Combine prompt_text and example_output with marker
    let finalPromptText = formData.prompt_text;
    if (formData.example_output.trim()) {
      finalPromptText += '\n\n---EXAMPLE---\n\n' + formData.example_output;
    }

    const promptData = {
      title: formData.title,
      prompt_text: finalPromptText,
      category: formData.category,
      tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean),
      source: formData.source || null
    };

    await promptsAPI.createPrompt(promptData);
    
    // Reset form instead of redirect
    setFormData({
      title: '',
      prompt_text: '',
      example_output: '',
      category: '',
      tags: '',
      source: ''
    });
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  } catch (err) {
    setError(err.message || 'Failed to create prompt');
  } finally {
    setSubmitting(false);
  }
};

  // Hierarchical category structure
  const categoryHierarchy = {
    'Data Collection': [
      'Data Extraction & APIs',
      'Interview Protocols'
    ],
    'Data Preparation': [
      'Text Preprocessing',
      'Data Cleaning',
      'Data Formatting'
    ],
    'Text Analysis': [
      'Text Summarization',
      'Text Classification',
      'Sentiment Analysis',
      'Word Frequency & Patterns'
    ],
    'Academic Writing': [
      'Literature Review',
      'Research Papers',
      'Reports & Presentations'
    ],
    'Advanced Methods': [
      'Model Fine-tuning',
      'Custom API Integration'
    ]
  };

  // Combine predefined and existing categories
  const allHierarchicalCategories = { ...categoryHierarchy };
  
  // Add any existing categories from database that aren't in predefined list
  categories.forEach(cat => {
    if (cat.includes(' > ')) {
      const [main, sub] = cat.split(' > ');
      if (!allHierarchicalCategories[main]) {
        allHierarchicalCategories[main] = [];
      }
      if (!allHierarchicalCategories[main].includes(sub)) {
        allHierarchicalCategories[main].push(sub);
      }
    }
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Add New Prompt
          </h2>
          <p className="text-gray-600 text-lg">
            Share a useful LLM prompt with the research community
          </p>
        </div>

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-6 py-4 rounded-lg mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">Prompt added successfully!</span>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          {/* Title */}
          <div className="mb-6">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="e.g., Survey Response Sentiment Analyzer"
              className="input-field"
            />
            <p className="mt-1 text-sm text-gray-500">
              A clear, descriptive title for your prompt
            </p>
          </div>

          {/* Category - Hierarchical Dropdown */}
          <div className="mb-6">
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
              Category <span className="text-red-500">*</span>
            </label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              required
              className="input-field"
            >
              <option value="">Select a category</option>
              {Object.entries(allHierarchicalCategories).map(([mainCat, subCats]) => (
                <optgroup key={mainCat} label={mainCat}>
                  {subCats.map((subCat) => {
                    const fullCategory = `${mainCat} > ${subCat}`;
                    const count = categoryCounts[fullCategory] || 0;
                    return (
                      <option key={fullCategory} value={fullCategory}>
                        {subCat} ({count})
                      </option>
                    );
                  })}
                </optgroup>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Choose the category that best fits your prompt
            </p>
          </div>

          {/* Prompt Text */}
          <div className="mb-6">
            <label htmlFor="prompt_text" className="block text-sm font-medium text-gray-700 mb-2">
              Prompt Text <span className="text-red-500">*</span>
            </label>
            <textarea
              id="prompt_text"
              name="prompt_text"
              value={formData.prompt_text}
              onChange={handleChange}
              required
              rows={12}
              placeholder="Enter your prompt here. Use {variable_name} for placeholders.

Example:
Analyze the sentiment of the following text: {text}

Classify it as positive, negative, or neutral and explain why."
              className="input-field font-mono text-sm"
            />
            <p className="mt-1 text-sm text-gray-500">
              💡 Tip: Use {'{curly_braces}'} to indicate variables that should be replaced
            </p>
          </div>

          {/* Add after the prompt_text textarea field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Example / Sample Output (Optional)
            </label>
            <textarea
              name="example_output"
              value={formData.example_output}
              onChange={handleChange}
              rows={6}
              className="input-field"
              placeholder="Add an example output to help users understand expected results..."
            />
          </div>

                  {/* Add success message before or after error message */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            Prompt added successfully!
          </div>
        )}

          {/* Tags */}
          <div className="mb-6">
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
              Tags (optional)
            </label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={formData.tags}
              onChange={handleChange}
              placeholder="e.g., survey, sentiment, classification"
              className="input-field"
            />
            <p className="mt-1 text-sm text-gray-500">
              Separate tags with commas. This helps others find your prompt.
            </p>
          </div>

          {/* Source */}
          <div className="mb-8">
            <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-2">
              Source (optional)
            </label>
            <input
              type="text"
              id="source"
              name="source"
              value={formData.source}
              onChange={handleChange}
              placeholder="e.g., Wolfram Prompt Repository, Custom, Research Paper"
              className="input-field"
            />
            <p className="mt-1 text-sm text-gray-500">
              Attribution or where you found this prompt
            </p>
          </div>

          {/* Submit Buttons */}
          <div className="flex items-center justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="btn-secondary"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Adding Prompt...
                </span>
              ) : (
                'Add Prompt'
              )}
            </button>
          </div>
        </form>

        {/* Guidelines */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            📝 Prompt Guidelines
          </h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Make your prompt clear and specific about what you want the LLM to do</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Include examples when helpful to demonstrate the desired output format</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Use variables {'{like_this}'} to make your prompt reusable</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Test your prompt before sharing to ensure it works well</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Add relevant tags to help others discover your prompt</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AddPromptPage;