import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import client from '../api/client';
import { getDashboardStats, getSessionHistory, downloadSessionCsv } from '../api/analytics';
import { getSessionRoster, deleteSession } from '../api/attendance';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Download, Eye, FileSpreadsheet, X, Calendar, User as UserIcon, Clock, Trash2 } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, BarElement, ArcElement,
  PointElement, LineElement, Title, Tooltip, Legend, Filler
);

export const AnalyticsPage = () => {
  const { theme } = useTheme();
  const { user } = useAuth();
  const isDark = theme === 'dark';
  
  const textColor = isDark ? '#cbd5e1' : '#475569'; // slate-300 / slate-600
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

  const [stats, setStats] = useState({
    present: 0, absent: 0, late: 0, excused: 0, attendance_rate: 0,
    weekly_trend: [{ date: 'Mon', rate: 0 }],
    method_breakdown: { face: 0, fingerprint: 0, manual: 0 }
  });

  const [sessions, setSessions] = useState([]);
  const [totalSessions, setTotalSessions] = useState(0);
  const [skip, setSkip] = useState(0);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionRoster, setSessionRoster] = useState([]);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats', err);
      }
    };
    fetchStats();
  }, []);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await getSessionHistory(skip, 10);
        setSessions(res.items);
        setTotalSessions(res.total);
      } catch (err) {
        console.error('Failed to fetch session history', err);
      }
    };
    fetchSessions();
  }, [skip]);

  const handleViewSession = async (session) => {
    setSelectedSession(session);
    try {
      const roster = await getSessionRoster(session.id);
      setSessionRoster(roster);
    } catch (err) {
      console.error('Failed to fetch roster details', err);
    }
  };

  const handleDownloadCsv = async (sessionId, e) => {
    if (e) e.stopPropagation();
    setIsDownloading(true);
    try {
      await downloadSessionCsv(sessionId);
    } catch (err) {
      console.error('Failed to download CSV', err);
      alert("Failed to download CSV. Please check console for details.");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      return;
    }
    try {
      await deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
    } catch (err) {
      console.error('Failed to delete session', err);
      alert('Failed to delete session.');
    }
  };

  const statusChartData = {
    labels: ['Present', 'Absent', 'Late', 'Excused'],
    datasets: [{
      data: [stats.present, stats.absent, stats.late, stats.excused],
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',   // green
        'rgba(239, 68, 68, 0.8)',   // red
        'rgba(245, 158, 11, 0.8)',  // amber
        'rgba(99, 102, 241, 0.8)',  // indigo
      ],
      hoverBackgroundColor: [
        'rgba(34, 197, 94, 1)',
        'rgba(239, 68, 68, 1)',
        'rgba(245, 158, 11, 1)',
        'rgba(99, 102, 241, 1)',
      ],
      borderWidth: 2,
      borderColor: 'hsl(var(--background))',
    }]
  };

  const weeklyTrendData = {
    labels: stats.weekly_trend ? stats.weekly_trend.map(t => t.date) : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    datasets: [{
      label: 'Attendance Rate (%)',
      data: stats.weekly_trend ? stats.weekly_trend.map(t => t.rate) : [0, 0, 0, 0, 0],
      borderColor: 'rgba(99, 102, 241, 1)',
      backgroundColor: 'rgba(99, 102, 241, 0.15)',
      fill: true,
      tension: 0.4,
      pointBackgroundColor: 'rgba(255, 255, 255, 1)',
      pointBorderColor: 'rgba(99, 102, 241, 1)',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
    }]
  };

  const methodChartData = {
    labels: ['Face Recognition', 'Fingerprint', 'Manual'],
    datasets: [{
      label: 'Check-in Count',
      data: stats.method_breakdown 
        ? [stats.method_breakdown.face, stats.method_breakdown.fingerprint, stats.method_breakdown.manual]
        : [0, 0, 0],
      backgroundColor: [
        'rgba(14, 165, 233, 0.8)',  // light blue
        'rgba(168, 85, 247, 0.8)',  // purple
        'rgba(100, 116, 139, 0.8)', // slate
      ],
      hoverBackgroundColor: [
        'rgba(14, 165, 233, 1)',
        'rgba(168, 85, 247, 1)',
        'rgba(100, 116, 139, 1)',
      ],
      borderWidth: 0,
      borderRadius: 6,
      barPercentage: 0.6,
    }]
  };

  const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: textColor,
          font: { family: 'Inter', size: 12 },
          usePointStyle: true,
          padding: 20,
        }
      },
      tooltip: {
        backgroundColor: isDark ? '#1e293b' : '#ffffff',
        titleColor: isDark ? '#f8fafc' : '#0f172a',
        bodyColor: isDark ? '#cbd5e1' : '#475569',
        borderColor: gridColor,
        borderWidth: 1,
        padding: 10,
        displayColors: true,
        usePointStyle: true,
      }
    }
  };

  const lineChartOptions = {
    ...commonChartOptions,
    scales: {
      x: {
        ticks: { color: textColor, font: { family: 'Inter' } },
        grid: { color: gridColor, drawBorder: false }
      },
      y: {
        beginAtZero: true,
        max: 100,
        ticks: { 
          color: textColor, 
          font: { family: 'Inter' },
          callback: (value) => `${value}%`
        },
        grid: { color: gridColor, borderDash: [5, 5], drawBorder: false }
      }
    }
  };

  const barChartOptions = {
    ...commonChartOptions,
    scales: {
      x: {
        ticks: { color: textColor, font: { family: 'Inter' } },
        grid: { display: false, drawBorder: false }
      },
      y: {
        beginAtZero: true,
        ticks: { 
          color: textColor, 
          font: { family: 'Inter' },
          stepSize: 20
        },
        grid: { color: gridColor, borderDash: [5, 5], drawBorder: false }
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
        <p className="text-muted-foreground mt-1">Attendance insights and trends</p>
      </div>

      {/* Overall Rate */}
      <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
        <CardContent className="p-6 flex items-center gap-6">
          <div className="w-20 h-20 rounded-full border-4 border-primary flex items-center justify-center">
            <span className="text-2xl font-bold text-primary">{stats.attendance_rate}%</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold">Overall Attendance Rate</h3>
            <p className="text-sm text-muted-foreground">Across all sessions</p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Attendance Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px] flex items-center justify-center">
              <Doughnut
                data={statusChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                      labels: { 
                        color: textColor, 
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        padding: 20
                      }
                    },
                    tooltip: {
                      backgroundColor: isDark ? '#1e293b' : '#ffffff',
                      titleColor: isDark ? '#f8fafc' : '#0f172a',
                      bodyColor: isDark ? '#cbd5e1' : '#475569',
                      borderColor: gridColor,
                      borderWidth: 1,
                      padding: 10,
                      displayColors: true,
                      usePointStyle: true,
                    }
                  },
                  cutout: '65%',
                }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Weekly Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <Line data={weeklyTrendData} options={lineChartOptions} />
            </div>
          </CardContent>
        </Card>

        {/* Attendance Method Breakdown */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Attendance Method Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <Bar data={methodChartData} options={barChartOptions} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Session Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Session History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50 text-muted-foreground">
                  <th className="py-3 px-4 font-medium text-left">Date & Time</th>
                  <th className="py-3 px-4 font-medium text-left">Course</th>
                  <th className="py-3 px-4 font-medium text-left">Teacher</th>
                  <th className="py-3 px-4 font-medium text-center">Stats</th>
                  <th className="py-3 px-4 font-medium text-center">Status</th>
                  <th className="py-3 px-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-muted-foreground">
                      No past sessions found.
                    </td>
                  </tr>
                ) : (
                  sessions.map((session) => {
                    const d = new Date(session.started_at);
                    const rate = session.enrolled_count > 0 
                      ? Math.round((session.recognized_count / session.enrolled_count) * 100) 
                      : 0;

                    return (
                      <tr key={session.id} className="border-b hover:bg-muted/30 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-medium">{d.toLocaleDateString()}</div>
                          <div className="text-xs text-muted-foreground">{d.toLocaleTimeString()}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium">{session.course_code}</div>
                          <div className="text-xs text-muted-foreground">{session.course_name}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <UserIcon className="h-4 w-4 text-muted-foreground" />
                            <span>{session.teacher_name}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="font-medium">{session.recognized_count} / {session.enrolled_count}</div>
                          <div className="text-xs text-muted-foreground">{rate}% Rate</div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge variant={session.status === 'COMPLETED' ? 'success' : 'warning'}>
                            {session.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right space-x-2">
                          <Button variant="outline" size="sm" onClick={() => handleViewSession(session)}>
                            <Eye className="h-4 w-4 mr-1" /> View
                          </Button>
                          <Button size="sm" disabled={isDownloading} onClick={(e) => handleDownloadCsv(session.id, e)}>
                            <Download className="h-4 w-4 mr-1" /> CSV
                          </Button>
                          {user?.role === 'admin' && (
                            <Button variant="destructive" size="sm" onClick={() => handleDeleteSession(session.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          {totalSessions > 10 && (
            <div className="mt-4 flex justify-between items-center text-sm text-muted-foreground">
              <span>Showing {skip + 1} to {Math.min(skip + 10, totalSessions)} of {totalSessions} entries</span>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={skip === 0}
                  onClick={() => setSkip(s => Math.max(0, s - 10))}
                >
                  Previous
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={skip + 10 >= totalSessions}
                  onClick={() => setSkip(s => s + 10)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Session Details Modal */}
      {selectedSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <Card className="w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl">
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b">
              <div>
                <CardTitle className="text-xl">Session Report</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedSession.course_code} — {new Date(selectedSession.started_at).toLocaleString()}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setSelectedSession(null)}>
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-auto p-0">
              {sessionRoster.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  Loading roster or no students found.
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-background/95 backdrop-blur shadow-sm">
                    <tr className="border-b text-muted-foreground">
                      <th className="py-3 px-4 font-medium text-left">Student</th>
                      <th className="py-3 px-4 font-medium text-left">ID</th>
                      <th className="py-3 px-4 font-medium text-center">Status</th>
                      <th className="py-3 px-4 font-medium text-center">Method</th>
                      <th className="py-3 px-4 font-medium text-right">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessionRoster.map(student => (
                      <tr key={student.student_uuid} className="border-b hover:bg-muted/30">
                        <td className="py-3 px-4 font-medium">
                          {student.first_name} {student.last_name}
                        </td>
                        <td className="py-3 px-4 text-muted-foreground font-mono">
                          {student.student_id}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge variant={
                            student.status === 'present' ? 'success' :
                            student.status === 'absent' ? 'destructive' : 'warning'
                          }>
                            {student.status.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="text-xs font-mono bg-muted px-2 py-1 rounded">
                            {student.method.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          {student.confidence ? `${(student.confidence * 100).toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
            
            <div className="p-4 border-t flex justify-between items-center bg-muted/20">
              <span className="text-sm text-muted-foreground font-medium">
                {selectedSession.recognized_count} Present / {sessionRoster.length} Total Enrolled
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setSelectedSession(null)}>Close</Button>
                <Button onClick={() => handleDownloadCsv(selectedSession.id)} disabled={isDownloading}>
                  <Download className="h-4 w-4 mr-2" />
                  {isDownloading ? 'Downloading...' : 'Export CSV'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
