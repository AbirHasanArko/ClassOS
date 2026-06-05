import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { getStudents, createStudent } from '../api/students';
import { uploadFaceImages } from '../api/face';
import { enrollFingerprint } from '../api/attendance';
import { UserPlus, Search, Fingerprint, ScanFace } from 'lucide-react';

export const StudentsPage = () => {
  const [students, setStudents] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newStudent, setNewStudent] = useState({
    student_id: '', first_name: '', last_name: '', email: ''
  });

  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showFaceUpload, setShowFaceUpload] = useState(false);
  const [faceFiles, setFaceFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isEnrollingFP, setIsEnrollingFP] = useState(false);

  const fetchStudents = async () => {
    try {
      const data = await getStudents(0, 50, search);
      setStudents(data.items || []);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch students', err);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [search]);

  const handleAddStudent = async (e) => {
    e.preventDefault();
    try {
      await createStudent(newStudent);
      setShowAddModal(false);
      setNewStudent({ student_id: '', first_name: '', last_name: '', email: '' });
      fetchStudents();
    } catch (err) {
      console.error('Failed to create student', err);
    }
  };

  const handleUploadFaces = async (e) => {
    e.preventDefault();
    if (!faceFiles || faceFiles.length === 0) return;
    setIsUploading(true);
    try {
      await uploadFaceImages(selectedStudent.id, faceFiles);
      setShowFaceUpload(false);
      setFaceFiles([]);
      fetchStudents();
    } catch (err) {
      console.error('Failed to upload faces', err);
      alert('Failed to upload face images.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleEnrollFingerprint = async (student) => {
    if (confirm(`Please ask ${student.first_name} to place their finger on the sensor. Click OK to start.`)) {
      setIsEnrollingFP(true);
      try {
        await enrollFingerprint(student.id);
        alert('Fingerprint enrolled successfully!');
        fetchStudents();
      } catch (err) {
        console.error('Failed to enroll fingerprint', err);
        alert('Failed to enroll fingerprint. Ensure sensor is connected or mock mode is enabled.');
      } finally {
        setIsEnrollingFP(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Students</h2>
          <p className="text-muted-foreground mt-1">{total} students registered</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Add Student
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by name or ID..."
          className="w-full h-10 pl-9 pr-4 rounded-md border border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Student Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="text-left p-4 font-medium text-muted-foreground">Student ID</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Name</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Email</th>
                  <th className="text-center p-4 font-medium text-muted-foreground">Face</th>
                  <th className="text-center p-4 font-medium text-muted-foreground">Fingerprint</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="p-4 font-mono text-xs">{student.student_id}</td>
                    <td className="p-4 font-medium">{student.first_name} {student.last_name}</td>
                    <td className="p-4 text-muted-foreground">{student.email}</td>
                    <td className="p-4 text-center">
                      {student.face_registered ? (
                        <Badge variant="success"><ScanFace className="h-3 w-3 mr-1" />Enrolled</Badge>
                      ) : (
                        <Button variant="outline" size="sm" onClick={() => { setSelectedStudent(student); setShowFaceUpload(true); }}>
                          <ScanFace className="mr-2 h-4 w-4" /> Enroll
                        </Button>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {student.fingerprint_registered ? (
                        <Badge variant="success"><Fingerprint className="h-3 w-3 mr-1" />Enrolled</Badge>
                      ) : (
                        <Button variant="outline" size="sm" disabled={isEnrollingFP} onClick={() => handleEnrollFingerprint(student)}>
                          <Fingerprint className="mr-2 h-4 w-4" /> Enroll
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {students.length === 0 && (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-muted-foreground">
                      No students found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Add Student Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="w-full max-w-md shadow-2xl">
            <CardHeader>
              <CardTitle>Add New Student</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddStudent} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Student ID</label>
                  <input
                    type="text" required
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="e.g., 2024-CS-001"
                    value={newStudent.student_id}
                    onChange={(e) => setNewStudent({ ...newStudent, student_id: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">First Name</label>
                    <input
                      type="text" required
                      className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      value={newStudent.first_name}
                      onChange={(e) => setNewStudent({ ...newStudent, first_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Last Name</label>
                    <input
                      type="text" required
                      className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      value={newStudent.last_name}
                      onChange={(e) => setNewStudent({ ...newStudent, last_name: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <input
                    type="email" required
                    className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="student@university.edu"
                    value={newStudent.email}
                    onChange={(e) => setNewStudent({ ...newStudent, email: e.target.value })}
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="outline" type="button" onClick={() => setShowAddModal(false)}>Cancel</Button>
                  <Button type="submit">Create Student</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Upload Face Modal */}
      {showFaceUpload && selectedStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="w-full max-w-md shadow-2xl">
            <CardHeader>
              <CardTitle>Enroll Face for {selectedStudent.first_name}</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUploadFaces} className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Select at least 1 clear, front-facing image of the student. For best results, select 5-10 images.
                </p>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Face Images</label>
                  <input
                    type="file" multiple accept="image/*" required
                    className="w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                    onChange={(e) => setFaceFiles(Array.from(e.target.files))}
                  />
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline" type="button" onClick={() => { setShowFaceUpload(false); setFaceFiles([]); }}>Cancel</Button>
                  <Button type="submit" disabled={isUploading || faceFiles.length === 0}>
                    {isUploading ? 'Uploading...' : 'Upload & Enroll'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
