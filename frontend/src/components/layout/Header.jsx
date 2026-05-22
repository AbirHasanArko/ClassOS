import { Moon, Sun, Bell } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { useLocation } from 'react-router-dom';

export const Header = () => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  // Simple breadcrumb logic based on path
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    const parts = path.split('/').filter(Boolean);
    if (parts.length > 0) {
      return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    }
    return '';
  };

  return (
    <header className="h-16 border-b bg-card/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-10">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{getPageTitle()}</h1>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 rounded-full hover:bg-accent text-muted-foreground relative">
          <Bell size={20} />
          <span className="absolute top-1.5 right-2 w-2 h-2 rounded-full bg-primary"></span>
        </button>
        <button 
          onClick={toggleTheme}
          className="p-2 rounded-full hover:bg-accent text-muted-foreground transition-colors"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>
    </header>
  );
};
