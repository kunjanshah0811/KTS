import { Link, useLocation } from 'react-router-dom';

const Header = () => {
  const location = useLocation();
  const isAddPage = location.pathname === '/add';

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-bold">🧠</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                LLM Prompts Repository
              </h1>
              <p className="text-sm text-gray-600">
                For Social Science Research
              </p>
            </div>
          </Link>
          
          <nav className="hidden md:flex items-center space-x-6">
            {isAddPage && (
              <Link 
                to="/" 
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium"
              >
                Browse Prompts
              </Link>
            )}
            <Link 
              to="/add" 
              className="btn-primary"
            >
              + Add Prompt
            </Link>
          </nav>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <Link to="/add" className="btn-primary text-sm">
              + Add
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;