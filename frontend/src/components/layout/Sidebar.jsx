import { Link, useLocation } from 'react-router-dom';
import { Home, Users, BookOpen, BarChart3, Settings, LogOut, CheckSquare } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../ui/Button';

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: Home, roles: ['admin', 'teacher', 'student'] },
    { name: 'Attendance', path: '/attendance', icon: CheckSquare, roles: ['admin', 'teacher'] },
    { name: 'Students', path: '/students', icon: Users, roles: ['admin', 'teacher'] },
    { name: 'Courses', path: '/courses', icon: BookOpen, roles: ['admin', 'teacher', 'student'] },
    { name: 'Analytics', path: '/analytics', icon: BarChart3, roles: ['admin', 'teacher'] },
    { name: 'Users', path: '/users', icon: Users, roles: ['admin'] },
    { name: 'Settings', path: '/settings', icon: Settings, roles: ['admin', 'teacher', 'student'] },
  ];

  // Filter based on role
  const visibleNav = navItems.filter(item => item.roles.includes(user?.role));

  return (
    <aside className="w-64 flex-shrink-0 bg-card border-r flex flex-col transition-all duration-300">
      <div className="h-16 flex items-center px-6 border-b">
        <div className="flex items-center gap-2 text-primary font-bold text-xl">
          <div className="w-8 h-8 rounded bg-primary text-primary-foreground flex items-center justify-center">
            C
          </div>
          <span>ClassOS</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {visibleNav.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <Link
              key={item.name}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon size={18} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t">
        <div className="flex items-center gap-3 mb-4 px-2">
          <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-bold text-secondary-foreground">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium truncate">{user?.name}</p>
            <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 text-sm text-destructive hover:bg-destructive/10 px-3 py-2 rounded-md transition-colors"
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </aside>
  );
};
