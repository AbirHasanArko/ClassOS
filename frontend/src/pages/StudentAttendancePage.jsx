import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { getMyAttendance } from '../api/students';
import { BookOpen } from 'lucide-react';

export const StudentAttendancePage = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAttendance = async () => {
    try {
      const data = await getMyAttendance();
      setCourses(data.courses || []);
    } catch (err) {
      console.error('Failed to fetch attendance', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">My Attendance</h2>
          <p className="text-muted-foreground mt-1">Track your attendance across enrolled courses</p>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-4 font-medium text-muted-foreground">Course Code</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Course Name</th>
                  <th className="text-center p-4 font-medium text-muted-foreground">Classes Present</th>
                  <th className="text-center p-4 font-medium text-muted-foreground">Total Classes</th>
                  <th className="text-center p-4 font-medium text-muted-foreground">Percentage</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-muted-foreground">Loading...</td>
                  </tr>
                ) : courses.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-muted-foreground">
                      No enrolled courses found.
                    </td>
                  </tr>
                ) : (
                  courses.map((course) => {
                    const pct = course.attendance_percentage.toFixed(1);
                    return (
                      <tr key={course.course_id} className="border-b hover:bg-muted/30 transition-colors">
                        <td className="p-4 font-mono text-xs">
                          <div className="flex items-center gap-2">
                            <BookOpen className="h-4 w-4 text-primary" />
                            {course.course_code}
                          </div>
                        </td>
                        <td className="p-4 font-medium">{course.course_name}</td>
                        <td className="p-4 text-center">{course.present_sessions}</td>
                        <td className="p-4 text-center">{course.total_sessions}</td>
                        <td className="p-4 text-center">
                          <div className={`font-semibold ${
                            course.attendance_percentage >= 75 ? 'text-green-600 dark:text-green-400' : 
                            course.attendance_percentage >= 60 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
                          }`}>
                            {pct}%
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
