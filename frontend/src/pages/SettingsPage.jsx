import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { Moon, Sun, Monitor } from 'lucide-react';

export const SettingsPage = () => {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground mt-1">Manage your account and preferences</p>
      </div>

      {/* Profile Card */}
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-2xl font-bold text-primary">
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="text-lg font-semibold">{user?.name}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <p className="text-xs text-muted-foreground capitalize mt-1">Role: {user?.role}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Theme</p>
              <p className="text-sm text-muted-foreground">
                Currently using {theme === 'dark' ? 'dark' : 'light'} mode
              </p>
            </div>
            <Button variant="outline" onClick={toggleTheme} className="gap-2">
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              Switch to {theme === 'dark' ? 'Light' : 'Dark'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* System Info */}
      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Application</p>
              <p className="font-medium">ClassOS v1.0.0</p>
            </div>
            <div>
              <p className="text-muted-foreground">Target Platform</p>
              <p className="font-medium">Raspberry Pi 5</p>
            </div>
            <div>
              <p className="text-muted-foreground">Backend</p>
              <p className="font-medium">FastAPI + PostgreSQL</p>
            </div>
            <div>
              <p className="text-muted-foreground">AI Engine</p>
              <p className="font-medium">face_recognition + YOLOv8n</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
