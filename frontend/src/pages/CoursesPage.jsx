import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { getCourses, createCourse, enrollStudents, getCourseStudents, updateCourse, deleteCourse } from '../api/courses';
import { getStudents } from '../api/students';
import { getCourseReport, downloadCourseReportCsv } from '../api/analytics';
import { getUsers } from '../api/users';
import { useAuth } from '../contexts/AuthContext';
import { BookOpen, Plus, Users, CheckSquare, Square, X, FileSpreadsheet, FileBarChart, Pencil, Trash } from 'lucide-react';

export const CoursesPage = () => {
  const { user: currentUser } = useAuth();
  const [courses, setCourses] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCourse, setNewCourse] = useState({
    course_code: '', course_name: '', schedule: '', teacher_id: ''
  });

  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [allStudents, setAllStudents] = useState([]);
  const [enrolledIds, setEnrolledIds] = useState(new Set());
  const [isSavingEnrollment, setIsSavingEnrollment] = useState(false);

  // Report Modal State
  const [showReportModal, setShowReportModal] = useState(false);
  const [selectedReportCourse, setSelectedReportCourse] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [isDownloadingReport, setIsDownloadingReport] = useState(false);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  // Edit/Delete State
  const [showEditModal, setShowEditModal] = useState(false);
  const [editCourseData, setEditCourseData] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchCourses = async () => {
    try {
      const data = await getCourses();
      setCourses(data.items || []);
    } catch (err) {
      console.error('Failed to fetch courses', err);
    }
  };

  const fetchTeachers = async () => {
    try {
      const data = await getUsers();
      setTeachers(data.filter(u => u.role === 'teacher' && u.profile_id));
    } catch (err) {
      console.error('Failed to fetch teachers', err);
    }
  };

  useEffect(() => {
    fetchCourses();
    if (currentUser?.role === 'admin') {
      fetchTeachers();
    }
  }, [currentUser]);

  const handleAddCourse = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...newCourse };
      if (!payload.teacher_id) delete payload.teacher_id;
      await createCourse(payload);
      setShowAddModal(false);
      setNewCourse({ course_code: '', course_name: '', schedule: '', teacher_id: '' });
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

  const handleOpenReportModal = async (course) => {
    setSelectedReportCourse(course);
    setShowReportModal(true);
    setIsLoadingReport(true);
    setReportData(null);
    try {
      const data = await getCourseReport(course.id);
      setReportData(data);
    } catch (err) {
      console.error('Failed to load course report', err);
    } finally {
      setIsLoadingReport(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!selectedReportCourse) return;
    setIsDownloadingReport(true);
    try {
      await downloadCourseReportCsv(selectedReportCourse.id);
    } catch (err) {
      console.error('Failed to download course report CSV', err);
    } finally {
      setIsDownloadingReport(false);
    }
  };

  const handleOpenEditModal = (course) => {
    setEditCourseData({ ...course });
    setShowEditModal(true);
  };

  const handleSaveEditCourse = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...editCourseData };
      if (!payload.teacher_id) delete payload.teacher_id;
      await updateCourse(editCourseData.id, payload);
      setShowEditModal(false);
      fetchCourses();
    } catch (err) {
      console.error('Failed to update course', err);
    }
  };

  const handleDeleteCourse = async (course) => {
    if (confirm(`Are you sure you want to delete ${course.course_code} - ${course.course_name}? This will delete all associated enrollments and sessions.`)) {
      setIsDeleting(true);
      try {
        await deleteCourse(course.id);
        fetchCourses();
      } catch (err) {
        console.error('Failed to delete course', err);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const getTeacherName = (teacherId) => {
    if (currentUser?.role === 'teacher') return 'Your Course';
    if (!teacherId) return 'No Teacher Assigned';
    const teacher = teachers.find(t => t.profile_id === teacherId);
    return teacher ? `${teacher.first_name} ${teacher.last_name}` : 'Unknown Teacher';
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
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono bg-muted px-2 py-1 rounded">{course.course_code}</span>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => { e.stopPropagation(); handleOpenEditModal(course); }}>
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-6 w-6 text-red-500 hover:text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30" onClick={(e) => { e.stopPropagation(); handleDeleteCourse(course); }} disabled={isDeleting}>
                      <Trash className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
              <CardTitle className="text-lg mt-3">{course.course_name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-medium text-foreground mb-1">
                {getTeacherName(course.teacher_id)}
              </p>
              <p className="text-sm text-muted-foreground mb-4">{course.schedule || 'No schedule set'}</p>
              <div className="flex flex-col gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={(e) => { e.stopPropagation(); handleOpenEnrollModal(course); }}
                >
                  <Users className="h-4 w-4 mr-2" />
                  Manage Students
                </Button>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  className="w-full"
                  onClick={(e) => { e.stopPropagation(); handleOpenReportModal(course); }}
                >
                  <FileBarChart className="h-4 w-4 mr-2" />
                  View Report
                </Button>
              </div>
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
                {currentUser?.role === 'admin' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Assign Teacher (Optional)</label>
                    <select
                      className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      value={newCourse.teacher_id || ''}
                      onChange={(e) => setNewCourse({ ...newCourse, teacher_id: e.target.value })}
                    >
                      <option value="">-- No Teacher --</option>
                      {teachers.map(t => (
                        <option key={t.profile_id} value={t.profile_id}>{t.first_name} {t.last_name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="outline" type="button" onClick={() => setShowAddModal(false)}>Cancel</Button>
                  <Button type="submit">Create Course</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Edit Course Modal */}
      {showEditModal && editCourseData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="w-full max-w-md shadow-2xl">
            <CardHeader>
              <CardTitle>Edit Course</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveEditCourse} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Course Code</label>
                  <input
                    type="text" disabled
                    className="w-full h-10 rounded-md border border-input bg-muted px-3 py-2 text-sm text-muted-foreground"
                    value={editCourseData.course_code}
                  />
                  <p className="text-xs text-muted-foreground">Course code cannot be changed.</p>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Course Name</label>
                  <input
                    type="text" required
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={editCourseData.course_name}
                    onChange={(e) => setEditCourseData({ ...editCourseData, course_name: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Schedule</label>
                  <input
                    type="text"
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={editCourseData.schedule || ''}
                    onChange={(e) => setEditCourseData({ ...editCourseData, schedule: e.target.value })}
                  />
                </div>
                {currentUser?.role === 'admin' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Assign Teacher (Optional)</label>
                    <select
                      className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      value={editCourseData.teacher_id || ''}
                      onChange={(e) => setEditCourseData({ ...editCourseData, teacher_id: e.target.value })}
                    >
                      <option value="">-- No Teacher --</option>
                      {teachers.map(t => (
                        <option key={t.profile_id} value={t.profile_id}>{t.first_name} {t.last_name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="outline" type="button" onClick={() => setShowEditModal(false)}>Cancel</Button>
                  <Button type="submit">Save Changes</Button>
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

      {/* Course Report Modal */}
      {showReportModal && selectedReportCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <Card className="w-full max-w-6xl max-h-[90vh] flex flex-col shadow-2xl">
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b">
              <div>
                <CardTitle className="text-xl">Course Attendance Report</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedReportCourse.course_code} — {selectedReportCourse.course_name}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowReportModal(false)}>
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-auto p-0">
              {isLoadingReport ? (
                <div className="p-8 text-center text-muted-foreground">Loading report data...</div>
              ) : !reportData || reportData.students.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  No attendance data or students found for this course.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-background/95 backdrop-blur shadow-sm z-10">
                      <tr className="border-b text-muted-foreground">
                        <th className="py-3 px-4 font-medium text-left sticky left-0 bg-background/95 backdrop-blur">Student ID</th>
                        <th className="py-3 px-4 font-medium text-left sticky left-24 bg-background/95 backdrop-blur">Name</th>
                        {reportData.session_dates.map((date, idx) => (
                          <th key={idx} className="py-3 px-4 font-medium text-center whitespace-nowrap">{date}</th>
                        ))}
                        <th className="py-3 px-4 font-medium text-center border-l">Percentage</th>
                        <th className="py-3 px-4 font-medium text-center">Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.students.map((student) => (
                        <tr key={student.student_id} className="border-b hover:bg-muted/30">
                          <td className="py-3 px-4 font-mono text-xs sticky left-0 bg-background">{student.student_id}</td>
                          <td className="py-3 px-4 font-medium whitespace-nowrap sticky left-24 bg-background">
                            {student.first_name} {student.last_name}
                          </td>
                          {reportData.session_dates.map((date, idx) => {
                            const status = student.sessions[date];
                            return (
                              <td key={idx} className="py-3 px-4 text-center">
                                {status === 'PRESENT' || status === 'LATE' ? (
                                  <span className="text-green-600 dark:text-green-400 font-bold">P</span>
                                ) : status === 'EXCUSED' ? (
                                  <span className="text-blue-600 dark:text-blue-400 font-bold">E</span>
                                ) : (
                                  <span className="text-red-600 dark:text-red-400 font-bold">A</span>
                                )}
                              </td>
                            );
                          })}
                          <td className="py-3 px-4 text-center border-l">
                            <span className={`font-semibold ${student.attendance_percentage < 60 ? 'text-red-600 dark:text-red-400' : ''}`}>
                              {student.attendance_percentage}%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center font-bold">
                            {student.attendance_score}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
            
            <div className="p-4 border-t flex justify-between items-center bg-muted/20">
              <span className="text-sm text-muted-foreground font-medium">
                {reportData?.students.length || 0} students
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowReportModal(false)}>Close</Button>
                <Button 
                  onClick={handleDownloadReport} 
                  disabled={isDownloadingReport || !reportData || reportData.students.length === 0}
                >
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
                  {isDownloadingReport ? 'Downloading...' : 'Export CSV'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
