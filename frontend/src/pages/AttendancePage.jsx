import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useWebSocket } from '../contexts/WebSocketContext';
import { getCourses } from '../api/courses';
import { startSession, endSession, triggerFingerprintScan } from '../api/attendance';
import { Camera, StopCircle, Fingerprint, Users, UserCheck, AlertTriangle } from 'lucide-react';

export const AttendancePage = () => {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [activeSession, setActiveSession] = useState(null);
  const [attendanceList, setAttendanceList] = useState([]);
  const [headCount, setHeadCount] = useState(0);
  const [recognizedCount, setRecognizedCount] = useState(0);
  const [fingerprintNeeded, setFingerprintNeeded] = useState(false);
  const [loading, setLoading] = useState(false);

  const { messages, connect, disconnect, isConnected } = useWebSocket();

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const data = await getCourses();
        setCourses(data.items || []);
      } catch (err) {
        console.error('Failed to fetch courses', err);
      }
    };
    fetchCourses();
  }, []);

  // Process incoming WebSocket messages
  useEffect(() => {
    if (messages.length === 0) return;
    const latest = messages[messages.length - 1];

    switch (latest.type) {
      case 'attendance_marked':
        setAttendanceList((prev) => {
          const exists = prev.find((a) => a.student_id === latest.data.student_id);
          if (exists) return prev;
          return [...prev, {
            student_id: latest.data.student_id,
            method: latest.data.method,
            confidence: latest.data.confidence,
            time: new Date().toLocaleTimeString(),
          }];
        });
        setRecognizedCount((c) => c + 1);
        break;
      case 'head_count_mismatch':
        setHeadCount(latest.data.head_count);
        break;
      case 'fingerprint_required':
        setFingerprintNeeded(true);
        break;
      case 'unknown_face':
        break;
      default:
        break;
    }
  }, [messages]);

  const handleStartSession = async () => {
    if (!selectedCourse) return;
    setLoading(true);
    try {
      const session = await startSession(selectedCourse);
      setActiveSession(session);
      setAttendanceList([]);
      setHeadCount(0);
      setRecognizedCount(0);
      connect(session.id);
    } catch (err) {
      console.error('Failed to start session', err);
    }
    setLoading(false);
  };

  const handleEndSession = async () => {
    if (!activeSession) return;
    setLoading(true);
    try {
      await endSession(activeSession.id);
      disconnect();
      setActiveSession(null);
    } catch (err) {
      console.error('Failed to end session', err);
    }
    setLoading(false);
  };

  const handleFingerprintScan = async () => {
    try {
      const result = await triggerFingerprintScan();
      if (result.success) {
        setFingerprintNeeded(false);
      }
    } catch (err) {
      console.error('Fingerprint scan failed', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Live Attendance</h2>
          <p className="text-muted-foreground mt-1">Start a session to begin scanning</p>
        </div>
        {activeSession && (
          <Badge variant="success" className="animate-pulse text-sm px-3 py-1">
            ● Session Active
          </Badge>
        )}
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4 flex flex-wrap items-center gap-4">
          <select
            className="flex h-10 w-64 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            disabled={!!activeSession}
          >
            <option value="">Select Course...</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.course_code} — {c.course_name}
              </option>
            ))}
          </select>

          {!activeSession ? (
            <Button onClick={handleStartSession} disabled={!selectedCourse || loading}>
              <Camera className="mr-2 h-4 w-4" />
              {loading ? 'Starting...' : 'Start Attendance'}
            </Button>
          ) : (
            <Button variant="destructive" onClick={handleEndSession} disabled={loading}>
              <StopCircle className="mr-2 h-4 w-4" />
              {loading ? 'Stopping...' : 'End Session'}
            </Button>
          )}

          {isConnected && (
            <span className="text-xs text-green-500 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse"></span>
              WebSocket Connected
            </span>
          )}
        </CardContent>
      </Card>

      {/* Main content — Live feed + Attendance */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Live Video Feed */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Live Camera Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center">
              {activeSession ? (
                <img
                  src="/api/stream/live"
                  alt="Live Camera Feed"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : (
                <div className="text-muted-foreground text-sm flex flex-col items-center gap-2">
                  <Camera size={48} className="opacity-30" />
                  <p>Start a session to activate the camera</p>
                </div>
              )}
              <div className="hidden text-muted-foreground text-sm flex-col items-center gap-2">
                <Camera size={48} className="opacity-30" />
                <p>Camera feed unavailable</p>
              </div>
            </div>

            {/* Head Count Bar */}
            {activeSession && (
              <div className="mt-4 flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Users size={16} className="text-purple-500" />
                  <span className="text-sm font-medium">Head Count: {headCount}</span>
                </div>
                <div className="flex items-center gap-2">
                  <UserCheck size={16} className="text-green-500" />
                  <span className="text-sm font-medium">Recognized: {recognizedCount}</span>
                </div>
                {headCount > recognizedCount && (
                  <div className="flex items-center gap-2 text-orange-500">
                    <AlertTriangle size={16} />
                    <span className="text-sm font-medium">Mismatch detected!</span>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Attendance List Panel */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Attendance Log</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[500px] overflow-y-auto">
            {attendanceList.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No attendance recorded yet.
              </p>
            ) : (
              <div className="space-y-2">
                {attendanceList.map((entry, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                    <div>
                      <p className="text-sm font-medium">{entry.student_id.slice(0, 8)}...</p>
                      <p className="text-xs text-muted-foreground">{entry.time}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={entry.method === 'face' ? 'success' : 'warning'}>
                        {entry.method.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {(entry.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Fingerprint Prompt */}
            {fingerprintNeeded && (
              <div className="mt-4 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-orange-500 mb-2">
                  <Fingerprint size={20} />
                  <span className="font-medium text-sm">Fingerprint Verification Needed</span>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  A face was detected with low confidence. Please ask the student to place their finger on the sensor.
                </p>
                <Button size="sm" onClick={handleFingerprintScan}>
                  <Fingerprint className="mr-1 h-3 w-3" />
                  Scan Fingerprint
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
