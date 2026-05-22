import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import client from '../api/client';
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
  const [stats, setStats] = useState({
    present: 0, absent: 0, late: 0, excused: 0, attendance_rate: 0
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await client.get('/analytics/dashboard/stats');
        setStats(res.data);
      } catch (err) {
        console.error('Failed to fetch stats', err);
      }
    };
    fetchStats();
  }, []);

  const statusChartData = {
    labels: ['Present', 'Absent', 'Late', 'Excused'],
    datasets: [{
      data: [stats.present, stats.absent, stats.late, stats.excused],
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',
        'rgba(239, 68, 68, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(99, 102, 241, 0.8)',
      ],
      borderWidth: 0,
    }]
  };

  const weeklyTrendData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    datasets: [{
      label: 'Attendance Rate (%)',
      data: [85, 92, 78, 95, 88],
      borderColor: 'rgba(99, 102, 241, 1)',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      fill: true,
      tension: 0.4,
      pointBackgroundColor: 'rgba(99, 102, 241, 1)',
      pointBorderWidth: 0,
      pointRadius: 4,
    }]
  };

  const methodChartData = {
    labels: ['Face Recognition', 'Fingerprint', 'Manual'],
    datasets: [{
      label: 'Count',
      data: [65, 15, 20],
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',
        'rgba(245, 158, 11, 0.8)',
        'rgba(99, 102, 241, 0.8)',
      ],
      borderWidth: 0,
      borderRadius: 6,
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: 'hsl(var(--muted-foreground))',
          font: { family: 'Inter' }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: 'hsl(var(--muted-foreground))' },
        grid: { color: 'hsl(var(--border))' }
      },
      y: {
        ticks: { color: 'hsl(var(--muted-foreground))' },
        grid: { color: 'hsl(var(--border))' }
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
                      labels: { color: 'hsl(var(--muted-foreground))', font: { family: 'Inter' } }
                    }
                  },
                  cutout: '60%',
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
              <Line data={weeklyTrendData} options={chartOptions} />
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
              <Bar data={methodChartData} options={chartOptions} />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
