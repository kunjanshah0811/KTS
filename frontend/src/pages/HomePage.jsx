import { useState, useEffect } from 'react';
import { usePrompts, useCategories } from '../hooks/usePrompts';
import { promptsAPI } from '../utils/api';
import PromptCard from '../components/PromptCard';
import PromptModal from '../components/PromptModal';
import SearchBar from '../components/SearchBar';

const HomePage = () => {
  const [filters, setFilters] = useState({});
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [sourceFilter, setSourceFilter] = useState(''); // '' or 'wolfram'
  const [categoryCounts, setCategoryCounts] = useState({});
  
  const { prompts, loading, error, setPrompts } = usePrompts(filters);
  const { categories } = useCategories();

  // Fetch category counts
  useEffect(() => {
    const fetchCategoryCounts = async () => {
      try {
        const stats = await promptsAPI.getStats();
        setCategoryCounts(stats.categories || {});
      } catch (err) {
        console.error('Error fetching category counts:', err);
      }
    };
    fetchCategoryCounts();
  }, []);

  const handleSearch = (searchTerm) => {
    setFilters(prev => ({
      ...prev,
      search: searchTerm || undefined
    }));
  };

  const handleCategoryChange = (category) => {
    setFilters(prev => ({
      ...prev,
      category: category || undefined
    }));
  };

  const handleSortChange = (sort) => {
    setFilters(prev => ({
      ...prev,
      sort
    }));
  };

  const handleSourceFilter = (source) => {
    setSourceFilter(source);
  };

  const openPromptModal = async (prompt) => {
    try {
      // Call API to get full prompt details (this increments view count)
      const updatedPrompt = await promptsAPI.getPrompt(prompt.id);
      
      // Update the prompt in the list with new view count
      setPrompts(prevPrompts => 
        prevPrompts.map(p => p.id === prompt.id ? updatedPrompt : p)
      );
      
      // Show the updated prompt in modal
      setSelectedPrompt(updatedPrompt);
    } catch (error) {
      console.error('Error loading prompt:', error);
      // Fallback to showing the prompt anyway
      setSelectedPrompt(prompt);
    }
  };

  const closePromptModal = () => {
    setSelectedPrompt(null);
  };

  // Filter prompts by source
  const filteredPrompts = sourceFilter === 'wolfram' 
    ? prompts.filter(p => p.source && p.source.toLowerCase().includes('wolfram'))
    : prompts;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Discover LLM Prompts
          </h2>
          <p className="text-gray-600 text-lg">
            Browse and copy prompts designed for Social Science Research
          </p>
        </div>

        {/* Search and Filters */}
        <SearchBar
          onSearch={handleSearch}
          onCategoryChange={handleCategoryChange}
          onSortChange={handleSortChange}
          onViewChange={setViewMode}
          onSourceFilter={handleSourceFilter}
          viewMode={viewMode}
          sourceFilter={sourceFilter}
          categories={categories}
          categoryCounts={categoryCounts}
        />

        {/* Stats */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              {loading ? 'Loading...' : `${filteredPrompts.length} prompt${filteredPrompts.length !== 1 ? 's' : ''} found`}
              {sourceFilter === 'wolfram' && <span className="ml-2 text-orange-600 font-medium">(Wolfram only)</span>}
            </span>
            <span className="text-xs">
              💡 Click any prompt to view details and copy
            </span>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            Error loading prompts: {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredPrompts.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No prompts found
            </h3>
            <p className="text-gray-600 mb-6">
              {sourceFilter === 'wolfram' 
                ? 'No Wolfram prompts found. Try clearing the filter.' 
                : 'Try adjusting your search or filters'}
            </p>
            {sourceFilter && (
              <button
                onClick={() => setSourceFilter('')}
                className="btn-primary"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}

        {/* Prompts Grid/List */}
        {!loading && filteredPrompts.length > 0 && (
          <div className={
            viewMode === 'grid' 
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
              : 'space-y-4'
          }>
            {filteredPrompts.map((prompt) => (
              <PromptCard
                key={prompt.id}
                prompt={prompt}
                onClick={() => openPromptModal(prompt)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Prompt Detail Modal */}
      {selectedPrompt && (
        <PromptModal
          prompt={selectedPrompt}
          onClose={closePromptModal}
        />
      )}
    </div>
  );
};

export default HomePage;