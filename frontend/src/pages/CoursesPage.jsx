import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { getCourses, createCourse, enrollStudents, getCourseStudents } from '../api/courses';
import { getStudents } from '../api/students';
import { BookOpen, Plus, Users, CheckSquare, Square, X } from 'lucide-react';

export const CoursesPage = () => {
  const [courses, setCourses] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCourse, setNewCourse] = useState({
    course_code: '', course_name: '', schedule: ''
  });

  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [allStudents, setAllStudents] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState(new Set());
  const [isSavingEnrollment, setIsSavingEnrollment] = useState(false);

  const fetchCourses = async () => {
    try {
      const data = await getCourses();
      setCourses(data.items || []);
    } catch (err) {
      console.error('Failed to fetch courses', err);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const handleAddCourse = async (e) => {
    e.preventDefault();
    try {
      await createCourse(newCourse);
      setShowAddModal(false);
      setNewCourse({ course_code: '', course_name: '', schedule: '' });
      fetchCourses();
    } catch (err) {
      console.error('Failed to create course', err);
    }
  };

  const handleOpenEnrollModal = async (course) => {
    setSelectedCourse(course);
    setShowEnrollModal(true);
    setEnrolledIds(new Set()); // Clear first
    
    try {
      // Fetch all students (backend enforces max limit of 100)
      const studentsData = await getStudents(0, 100);
      setAllStudents(studentsData.items || []);
      
      // Fetch currently enrolled student IDs
      const enrolled = await getCourseStudents(course.id);
      setEnrolledIds(new Set(enrolled));
    } catch (err) {
      console.error('Failed to load enrollment data', err);
    }
  };

  const toggleStudentEnrollment = (studentId) => {
    setEnrolledIds(prev => {
      const next = new Set(prev);
      if (next.has(studentId)) {
        next.delete(studentId);
      } else {
        next.add(studentId);
      }
      return next;
    });
  };

  const handleSaveEnrollments = async () => {
    if (!selectedCourse) return;
    setIsSavingEnrollment(true);
    try {
      await enrollStudents(selectedCourse.id, Array.from(enrolledIds));
      setShowEnrollModal(false);
      setSelectedCourse(null);
    } catch (err) {
      console.error('Failed to save enrollments', err);
    } finally {
      setIsSavingEnrollment(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Courses</h2>
          <p className="text-muted-foreground mt-1">{courses.length} courses available</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Course
        </Button>
      </div>

      {/* Course Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {courses.map((course) => (
          <Card key={course.id} className="hover:shadow-md transition-shadow cursor-pointer group">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <BookOpen className="h-5 w-5 text-primary" />
                </div>
                <span className="text-xs font-mono bg-muted px-2 py-1 rounded">{course.course_code}</span>
              </div>
              <CardTitle className="text-lg mt-3">{course.course_name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">{course.schedule || 'No schedule set'}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full"
                onClick={(e) => { e.stopPropagation(); handleOpenEnrollModal(course); }}
              >
                <Users className="h-4 w-4 mr-2" />
                Manage Students
              </Button>
            </CardContent>
          </Card>
        ))}
        {courses.length === 0 && (
          <Card className="col-span-full">
            <CardContent className="p-8 text-center text-muted-foreground">
              No courses found. Add one to get started.
            </CardContent>
          </Card>
        )}
      </div>

      {/* Add Course Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="w-full max-w-md shadow-2xl">
            <CardHeader>
              <CardTitle>Add New Course</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddCourse} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Course Code</label>
                  <input
                    type="text" required
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="e.g., CS101"
                    value={newCourse.course_code}
                    onChange={(e) => setNewCourse({ ...newCourse, course_code: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Course Name</label>
                  <input
                    type="text" required
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="e.g., Introduction to Computer Science"
                    value={newCourse.course_name}
                    onChange={(e) => setNewCourse({ ...newCourse, course_name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Schedule</label>
                  <input
                    type="text"
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="e.g., Mon/Wed 10:00-11:30"
                    value={newCourse.schedule}
                    onChange={(e) => setNewCourse({ ...newCourse, schedule: e.target.value })}
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="outline" type="button" onClick={() => setShowAddModal(false)}>Cancel</Button>
                  <Button type="submit">Create Course</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Enroll Students Modal */}
      {showEnrollModal && selectedCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b">
              <div>
                <CardTitle>Manage Enrollments</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedCourse.course_code} — {selectedCourse.course_name}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowEnrollModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-auto p-0">
              {allStudents.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  No students found in the system.
                </div>
              ) : (
                <div className="divide-y">
                  {allStudents.map(student => {
                    const isEnrolled = enrolledIds.has(student.id);
                    return (
                      <div 
                        key={student.id} 
                        className={`flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors ${isEnrolled ? 'bg-primary/5' : ''}`}
                        onClick={() => toggleStudentEnrollment(student.id)}
                      >
                        <div>
                          <p className="font-medium">{student.first_name} {student.last_name}</p>
                          <p className="text-sm text-muted-foreground">ID: {student.student_id}</p>
                        </div>
                        <div>
                          {isEnrolled ? (
                            <CheckSquare className="h-5 w-5 text-primary" />
                          ) : (
                            <Square className="h-5 w-5 text-muted-foreground" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
            
            <div className="p-4 border-t flex justify-between items-center bg-muted/20">
              <span className="text-sm text-muted-foreground font-medium">
                {enrolledIds.size} students selected
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowEnrollModal(false)}>Cancel</Button>
                <Button onClick={handleSaveEnrollments} disabled={isSavingEnrollment}>
                  {isSavingEnrollment ? 'Saving...' : 'Save Enrollments'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
