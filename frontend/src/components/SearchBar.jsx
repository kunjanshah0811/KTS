import { useState } from 'react';

const SearchBar = ({ onSearch, onCategoryChange, categories, onSortChange, onViewChange, viewMode, onSourceFilter, sourceFilter, categoryCounts = {} }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    onSearch(value);
  };

  // Parse hierarchical categories
  const parseCategories = () => {
    const hierarchy = {};
    
    categories.forEach(cat => {
      if (cat.includes(' > ')) {
        const [main, sub] = cat.split(' > ');
        if (!hierarchy[main]) {
          hierarchy[main] = [];
        }
        if (!hierarchy[main].includes(cat)) {
          hierarchy[main].push(cat);
        }
      } else {
        // Handle any non-hierarchical categories
        if (!hierarchy['Other']) {
          hierarchy['Other'] = [];
        }
        hierarchy['Other'].push(cat);
      }
    });
    
    return hierarchy;
  };

  const categoryHierarchy = parseCategories();

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mb-4">
        {/* Search Input */}
        <div className="md:col-span-5">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by title, category, or tags..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="input-field pl-10"
            />
            <svg 
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Category Filter - Hierarchical with Counts */}
        <div className="md:col-span-3">
          <select
            onChange={(e) => onCategoryChange(e.target.value)}
            className="input-field"
          >
            <option value="">All Categories</option>
            {Object.entries(categoryHierarchy).sort().map(([mainCat, subCats]) => (
              <optgroup key={mainCat} label={mainCat}>
                {subCats.sort().map((fullCategory) => {
                  const subCat = fullCategory.split(' > ')[1] || fullCategory;
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
        </div>

        {/* Sort */}
        <div className="md:col-span-2">
          <select
            onChange={(e) => onSortChange(e.target.value)}
            className="input-field"
          >
            <option value="date">Newest First</option>
            <option value="popularity">Most Popular</option>
          </select>
        </div>

        {/* View Toggle */}
        <div className="md:col-span-2 flex items-center justify-end space-x-2">
          <button
            onClick={() => onViewChange('grid')}
            className={`p-2 rounded-lg transition-colors ${
              viewMode === 'grid' 
                ? 'bg-primary-100 text-primary-700' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="Grid view"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
          <button
            onClick={() => onViewChange('list')}
            className={`p-2 rounded-lg transition-colors ${
              viewMode === 'list' 
                ? 'bg-primary-100 text-primary-700' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title="List view"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Wolfram Filter Button */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Filter by source:</span>
        <button
          onClick={() => onSourceFilter(sourceFilter === 'wolfram' ? '' : 'wolfram')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            sourceFilter === 'wolfram'
              ? 'bg-orange-100 text-orange-700 border-2 border-orange-300'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-2 border-transparent'
          }`}
        >
          {sourceFilter === 'wolfram' ? '✓ ' : ''}🟠 Wolfram Prompts
        </button>
        {sourceFilter && (
          <button
            onClick={() => onSourceFilter('')}
            className="text-sm text-gray-600 hover:text-gray-800 underline"
          >
            Clear filter
          </button>
        )}
      </div>
    </div>
  );
};

export default SearchBar;