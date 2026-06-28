import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { getCourses } from '../api/courses';
import { selfEnrollCourse, selfUnenrollCourse, getMyAttendance } from '../api/students';
import { BookOpen, UserPlus, UserMinus } from 'lucide-react';

export const StudentCoursesPage = () => {
  const [courses, setCourses] = useState([]);
  const [enrolledCourseIds, setEnrolledCourseIds] = useState(new Set());
  const [loadingId, setLoadingId] = useState(null);

  const fetchData = async () => {
    try {
      const [allCourses, attendanceData] = await Promise.all([
        getCourses(),
        getMyAttendance()
      ]);
      setCourses(allCourses.items || []);
      
      const enrolledIds = new Set(attendanceData.courses.map(c => c.course_id));
      setEnrolledCourseIds(enrolledIds);
    } catch (err) {
      console.error('Failed to fetch data', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleEnroll = async (courseId) => {
    setLoadingId(courseId);
    try {
      const res = await selfEnrollCourse(courseId);
      alert(res.message);
      fetchData(); // Refresh enrolled status
    } catch (err) {
      console.error('Failed to enroll', err);
      if (err.response?.data?.detail) {
        alert(err.response.data.detail);
      } else {
        alert('Failed to enroll in course. You might already be enrolled.');
      }
    } finally {
      setLoadingId(null);
    }
  };

  const handleUnenroll = async (courseId) => {
    if (!confirm('Are you sure you want to unenroll from this course? This will remove all your attendance data for this course.')) return;
    
    setLoadingId(courseId);
    try {
      await selfUnenrollCourse(courseId);
      alert('Successfully unenrolled from course.');
      fetchData(); // Refresh enrolled status
    } catch (err) {
      console.error('Failed to unenroll', err);
      alert('Failed to unenroll from course.');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Available Courses</h2>
          <p className="text-muted-foreground mt-1">Enroll in your classes</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {courses.map((course) => (
          <Card key={course.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <BookOpen className="h-5 w-5 text-primary" />
                </div>
                <span className="text-xs font-mono bg-muted px-2 py-1 rounded">{course.course_code}</span>
              </div>
              <CardTitle className="text-lg mt-3">{course.course_name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">{course.schedule || 'No schedule set'}</p>
              {enrolledCourseIds.has(course.id) ? (
                <div className="flex flex-col gap-2">
                  <div className="text-sm font-medium text-green-600 dark:text-green-500 flex items-center justify-center bg-green-50 dark:bg-green-900/20 py-2 rounded-md">
                    ✓ Enrolled
                  </div>
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    className="w-full"
                    onClick={() => handleUnenroll(course.id)}
                    disabled={loadingId === course.id}
                  >
                    <UserMinus className="h-4 w-4 mr-2" />
                    {loadingId === course.id ? 'Processing...' : 'Unenroll'}
                  </Button>
                </div>
              ) : (
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => handleEnroll(course.id)}
                  disabled={loadingId === course.id}
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  {loadingId === course.id ? 'Processing...' : 'Enroll'}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
        {courses.length === 0 && (
          <Card className="col-span-full">
            <CardContent className="p-8 text-center text-muted-foreground">
              No courses found.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
