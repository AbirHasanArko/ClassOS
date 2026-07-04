import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useWebSocket } from '../contexts/WebSocketContext';
import { getCourses } from '../api/courses';
import {
  startSession, endSession, triggerFingerprintScan,
  getSessionRoster, markAttendanceManual, switchSessionMode
} from '../api/attendance';
import {
  Camera, StopCircle, Fingerprint, Users, UserCheck,
  AlertTriangle, List, Clock, CheckCircle2, XCircle, MonitorSpeaker
} from 'lucide-react';

// ─── LCD Mirror Component ────────────────────────────────────────────────────
// Replicates the physical 20×4 LCD display in the browser dashboard.
// Updates in real-time via WebSocket 'lcd_update' events.
const LCDMirror = ({ lines }) => {
  const [line1, line2, line3, line4] = lines;
  return (
    <div className="bg-[#1a1a00] border-2 border-[#6b6b00] rounded-lg p-3 font-mono text-sm">
      <div className="text-[#e6e600] text-xs mb-1 opacity-60 tracking-widest uppercase">20×4 LCD Mirror</div>
      <div className="space-y-0.5">
        {[line1, line2, line3, line4].map((line, i) => (
          <div
            key={i}
            className="text-[#e6e600] bg-[#0a0a00] px-2 py-0.5 rounded tracking-wider"
            style={{ minHeight: '1.5rem', fontFamily: 'monospace', fontSize: '0.8rem' }}
          >
            {(line || '').padEnd(20, ' ')}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Head Count Result Panel ─────────────────────────────────────────────────
const HeadCountPanel = ({ presentCount, headCount, camera1Available }) => {
  if (!camera1Available) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-3">
        <Camera size={48} className="opacity-30" />
        <p className="text-sm font-medium">Camera 1 not available</p>
        <p className="text-xs opacity-60">Connect Camera 1 (CAM/DISP 1) to use head counting</p>
      </div>
    );
  }

  const isMatch = presentCount === headCount;
  const diff = Math.abs(headCount - presentCount);

  return (
    <div className="space-y-4">
      {/* Big number comparison */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-4 rounded-xl bg-green-500/10 border border-green-500/30">
          <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wider">Present</p>
          <p className="text-5xl font-bold text-green-400">{presentCount}</p>
        </div>
        <div className="text-center p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
          <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wider">Head Count</p>
          <p className="text-5xl font-bold text-purple-400">{headCount}</p>
        </div>
      </div>

      {/* Match / Mismatch result */}
      <div className={`flex flex-col items-center justify-center p-5 rounded-xl border-2 gap-2 ${
        isMatch
          ? 'bg-green-500/10 border-green-500/50'
          : 'bg-red-500/10 border-red-500/50'
      }`}>
        {isMatch ? (
          <>
            <CheckCircle2 size={40} className="text-green-400" />
            <p className="text-xl font-bold text-green-400">✓ Match!</p>
            <p className="text-sm text-muted-foreground">Head count matches attendance</p>
          </>
        ) : (
          <>
            <XCircle size={40} className="text-red-400" />
            <p className="text-xl font-bold text-red-400">✗ Mismatch!</p>
            <p className="text-sm text-muted-foreground">
              {headCount > presentCount
                ? `${diff} unrecognized person${diff !== 1 ? 's' : ''} in room`
                : `${diff} person${diff !== 1 ? 's' : ''} marked but left`}
            </p>
          </>
        )}
      </div>
    </div>
  );
};


// ─── Main Attendance Page ─────────────────────────────────────────────────────
export const AttendancePage = () => {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [activeSession, setActiveSession] = useState(null);
  const [sessionMode, setSessionMode] = useState('attendance'); // 'attendance' | 'headcount'
  const [modeSwitching, setModeSwitching] = useState(false);

  // Attendance state
  const [attendanceList, setAttendanceList] = useState([]);
  const [recognizedCount, setRecognizedCount] = useState(0);
  const [roster, setRoster] = useState([]);
  const [activeTab, setActiveTab] = useState('log'); // 'log' | 'roster'
  const [fingerprintNeeded, setFingerprintNeeded] = useState(false);

  // Head count state
  const [headCount, setHeadCount] = useState(0);
  const [headCountMatch, setHeadCountMatch] = useState(null);
  const [camera1Available, setCamera1Available] = useState(false);

  // LCD mirror state — 4 lines of 20 chars
  const [lcdLines, setLcdLines] = useState([
    '      ClassOS       ',
    ' AI Attendance Sys  ',
    '                    ',
    '      Ready...      ',
  ]);

  const [loading, setLoading] = useState(false);
  const [sessionError, setSessionError] = useState('');

  const { messages, connect, disconnect, isConnected } = useWebSocket();

  // ── Load courses on mount
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

  const fetchRoster = useCallback(async (sessionId) => {
    try {
      const data = await getSessionRoster(sessionId);
      setRoster(data);
    } catch (err) {
      console.error('Failed to fetch roster', err);
    }
  }, []);

  // ── Process incoming WebSocket messages
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
            student_name: latest.data.student_name || latest.data.student_id?.slice(0, 8),
            method: latest.data.method,
            confidence: latest.data.confidence,
            time: new Date().toLocaleTimeString(),
          }];
        });
        setRecognizedCount((c) => c + 1);
        if (activeSession) fetchRoster(activeSession.id);
        break;

      case 'fingerprint_required':
        setFingerprintNeeded(true);
        break;

      case 'head_count_update':
        setHeadCount(latest.data.head_count);
        setHeadCountMatch(latest.data.is_match);
        break;

      case 'mode_switched':
        setSessionMode(latest.data.mode);
        setRecognizedCount(latest.data.present_count || 0);
        setHeadCount(latest.data.head_count || 0);
        break;

      case 'camera_1_unavailable':
        setCamera1Available(false);
        break;

      case 'lcd_update':
        setLcdLines([
          latest.data.line1 || '',
          latest.data.line2 || '',
          latest.data.line3 || '',
          latest.data.line4 || '',
        ]);
        break;

      case 'unknown_face':
        break;

      default:
        break;
    }
  }, [messages, activeSession, fetchRoster]);

  // ── Session controls
  const handleStartSession = async () => {
    if (!selectedCourse) return;
    setLoading(true);
    setSessionError('');
    try {
      // Always start in attendance mode
      const session = await startSession(selectedCourse, 'attendance');
      setActiveSession(session);
      setSessionMode('attendance');
      setAttendanceList([]);
      setHeadCount(0);
      setRecognizedCount(0);
      setRoster([]);
      setCamera1Available(false);
      setFingerprintNeeded(false);
      setLcdLines([
        'Total Attendee:  0  ',
        '                    ',
        '   Mode: ATTENDANCE ',
        '                    ',
      ]);
      await fetchRoster(session.id);
      connect(session.id);
    } catch (err) {
      console.error('Failed to start session', err);
      const detail = err?.response?.data?.detail;
      let msg = 'Failed to start session.';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        msg = `Validation error: ${detail[0].loc?.slice(1).join(' → ')} — ${detail[0].msg}`;
      } else if (err?.response?.status) {
        msg = `Server error ${err.response.status}. Check backend logs.`;
      }
      setSessionError(msg);
    }
    setLoading(false);
  };

  const handleEndSession = async () => {
    if (!activeSession) return;
    setLoading(true);
    setSessionError('');
    try {
      await endSession(activeSession.id);
      disconnect();
      setActiveSession(null);
      setSessionMode('attendance');
      setLcdLines([
        '      ClassOS       ',
        ' AI Attendance Sys  ',
        '                    ',
        '      Ready...      ',
      ]);
    } catch (err) {
      console.error('Failed to end session', err);
      const detail = err?.response?.data?.detail;
      setSessionError(typeof detail === 'string' ? detail : 'Failed to end session.');
    }
    setLoading(false);
  };

  // ── Mode switching
  const handleSwitchMode = async (newMode) => {
    if (!activeSession || newMode === sessionMode || modeSwitching) return;
    setModeSwitching(true);
    setSessionError('');
    try {
      const result = await switchSessionMode(activeSession.id, newMode);
      setSessionMode(newMode);
      setCamera1Available(result.camera_1_available || false);
    } catch (err) {
      console.error('Failed to switch mode', err);
      const detail = err?.response?.data?.detail;
      setSessionError(typeof detail === 'string' ? detail : 'Failed to switch mode.');
    }
    setModeSwitching(false);
  };

  // ── Fingerprint
  const handleFingerprintScan = async () => {
    if (!activeSession) return;
    try {
      const result = await triggerFingerprintScan();
      if (result.success && result.student_id) {
        setFingerprintNeeded(false);
        // Explicitly mark attendance since the verify endpoint only returns the match
        await markAttendanceManual(activeSession.id, result.student_id, 'present', 'fingerprint');
        await fetchRoster(activeSession.id);
      } else {
        alert(result.message || 'Fingerprint not recognized or not found in database.');
      }
    } catch (err) {
      console.error('Fingerprint scan failed', err);
      alert('Error triggering fingerprint scan. Make sure the sensor is connected.');
    }
  };

  // ── Manual override
  const handleManualOverride = async (studentId, status) => {
    if (!activeSession) return;
    try {
      await markAttendanceManual(activeSession.id, studentId, status);
      await fetchRoster(activeSession.id);
    } catch (err) {
      console.error('Failed to override status', err);
    }
  };

  // ── Computed camera stream URL
  const streamUrl = sessionMode === 'headcount' ? '/api/stream/headcount' : '/api/stream/live';

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Live Attendance</h2>
          <p className="text-muted-foreground mt-1">
            {activeSession
              ? sessionMode === 'attendance'
                ? '📷 Take Attendance mode — Camera 0 (Face Recognition)'
                : '👥 Verify Head Count mode — Camera 1 (YOLOv8)'
              : 'Select a course and start a session to begin'}
          </p>
        </div>
        {activeSession && (
          <Badge variant="success" className="animate-pulse text-sm px-3 py-1">
            ● Session Active
          </Badge>
        )}
      </div>

      {/* Session Controls */}
      <Card>
        <CardContent className="p-4 flex flex-wrap items-center gap-4">
          <select
            id="course-select"
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
            <Button id="start-session-btn" onClick={handleStartSession} disabled={!selectedCourse || loading}>
              <Camera className="mr-2 h-4 w-4" />
              {loading ? 'Starting...' : 'Start Session'}
            </Button>
          ) : (
            <Button id="end-session-btn" variant="destructive" onClick={handleEndSession} disabled={loading}>
              <StopCircle className="mr-2 h-4 w-4" />
              {loading ? 'Stopping...' : 'End Session'}
            </Button>
          )}

          {isConnected && (
            <span className="text-xs text-green-500 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse" />
              WebSocket Connected
            </span>
          )}
        </CardContent>
      </Card>

      {/* ── Mode Selector (shown only when session is active) ── */}
      {activeSession && (
        <div className="flex gap-3">
          {/* Take Attendance */}
          <button
            id="mode-attendance-btn"
            onClick={() => handleSwitchMode('attendance')}
            disabled={modeSwitching || sessionMode === 'attendance'}
            className={`flex-1 flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 ${
              sessionMode === 'attendance'
                ? 'border-primary bg-primary/10 text-primary shadow-md'
                : 'border-border bg-muted/20 text-muted-foreground hover:border-primary/50 hover:bg-muted/40'
            }`}
          >
            <Camera size={28} />
            <div className="text-center">
              <p className="font-semibold text-sm">Take Attendance</p>
              <p className="text-xs opacity-70">Camera 0 · Face Recognition</p>
            </div>
            {sessionMode === 'attendance' && (
              <span className="text-[10px] bg-primary text-primary-foreground px-2 py-0.5 rounded-full font-medium">
                ACTIVE
              </span>
            )}
          </button>

          {/* Verify Head Count */}
          <button
            id="mode-headcount-btn"
            onClick={() => handleSwitchMode('headcount')}
            disabled={modeSwitching || sessionMode === 'headcount'}
            className={`flex-1 flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 ${
              sessionMode === 'headcount'
                ? 'border-purple-500 bg-purple-500/10 text-purple-400 shadow-md'
                : 'border-border bg-muted/20 text-muted-foreground hover:border-purple-500/50 hover:bg-muted/40'
            }`}
          >
            <Users size={28} />
            <div className="text-center">
              <p className="font-semibold text-sm">Verify Head Count</p>
              <p className="text-xs opacity-70">Camera 1 · YOLOv8</p>
            </div>
            {sessionMode === 'headcount' && (
              <span className="text-[10px] bg-purple-500 text-white px-2 py-0.5 rounded-full font-medium">
                ACTIVE
              </span>
            )}
          </button>
        </div>
      )}

      {/* Error banner */}
      {sessionError && (
        <div className="p-3 rounded-lg border border-destructive/40 bg-destructive/10 text-destructive text-sm flex items-start gap-2">
          <span className="font-semibold shrink-0">Error:</span>
          <span>{sessionError}</span>
          <button className="ml-auto text-destructive/60 hover:text-destructive" onClick={() => setSessionError('')}>✕</button>
        </div>
      )}

      {/* ── Main Content Area ── */}
      <div className="grid gap-6 lg:grid-cols-3">

        {/* Camera Feed + Stats */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              {sessionMode === 'headcount' ? (
                <><Users size={18} className="text-purple-400" /> Head Count Camera (Camera 1)</>
              ) : (
                <><Camera size={18} className="text-primary" /> Attendance Camera (Camera 0)</>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Video Feed */}
            <div className="aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center relative">
              {activeSession ? (
                <>
                  <img
                    key={streamUrl}  // remount when URL changes to force reconnect
                    src={streamUrl}
                    alt="Live Camera Feed"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      const sibling = e.target.nextElementSibling;
                      if (sibling) sibling.style.display = 'flex';
                    }}
                  />
                  <div className="hidden text-muted-foreground text-sm flex-col items-center gap-2 absolute inset-0 items-center justify-center">
                    <Camera size={48} className="opacity-30" />
                    <p>Camera feed unavailable</p>
                  </div>
                </>
              ) : (
                <div className="text-muted-foreground text-sm flex flex-col items-center gap-2">
                  <Camera size={48} className="opacity-30" />
                  <p>Start a session to activate the camera</p>
                </div>
              )}
            </div>

            {/* Stats bar */}
            {activeSession && (
              <div className="flex flex-wrap items-center gap-4 text-sm">
                {sessionMode === 'attendance' && (
                  <>
                    <div className="flex items-center gap-1.5">
                      <UserCheck size={15} className="text-green-500" />
                      <span className="font-medium">Recognized: {recognizedCount}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Users size={15} className="text-blue-400" />
                      <span className="font-medium">Enrolled: {roster.length}</span>
                    </div>
                  </>
                )}
                {sessionMode === 'headcount' && (
                  <>
                    <div className="flex items-center gap-1.5">
                      <UserCheck size={15} className="text-green-500" />
                      <span className="font-medium">Present: {recognizedCount}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Users size={15} className="text-purple-400" />
                      <span className="font-medium">Head Count: {headCount}</span>
                    </div>
                    {headCount !== recognizedCount && headCount > 0 && (
                      <div className="flex items-center gap-1.5 text-orange-400">
                        <AlertTriangle size={15} />
                        <span className="font-medium">
                          {headCount > recognizedCount
                            ? `${headCount - recognizedCount} unaccounted`
                            : `${recognizedCount - headCount} extra marked`}
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* LCD Mirror — always show when session active */}
            {activeSession && (
              <LCDMirror lines={lcdLines} />
            )}
          </CardContent>
        </Card>

        {/* Right Panel — changes based on mode */}
        <Card className="flex flex-col h-full max-h-[700px]">
          <CardHeader className="pb-0 border-b border-border/50">
            <div className="flex justify-between items-center mb-2">
              <CardTitle className="text-lg">
                {sessionMode === 'headcount' ? 'Head Count Result' : 'Attendance'}
              </CardTitle>
              {sessionMode === 'attendance' && (
                <div className="flex gap-1 bg-muted/50 p-1 rounded-md">
                  <button
                    id="tab-log-btn"
                    onClick={() => setActiveTab('log')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-sm flex items-center gap-1 transition-colors ${
                      activeTab === 'log' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <Clock size={14} /> Live Log
                  </button>
                  <button
                    id="tab-roster-btn"
                    onClick={() => setActiveTab('roster')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-sm flex items-center gap-1 transition-colors ${
                      activeTab === 'roster' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <List size={14} /> Sheet
                  </button>
                </div>
              )}
            </div>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto p-4">
            {/* ── HEAD COUNT MODE ── */}
            {sessionMode === 'headcount' ? (
              <HeadCountPanel
                presentCount={recognizedCount}
                headCount={headCount}
                camera1Available={camera1Available || headCount > 0}
              />
            ) : (
              /* ── ATTENDANCE MODE ── */
              <>
                {activeTab === 'log' ? (
                  <div className="space-y-4">
                    {/* Live log entries */}
                    {attendanceList.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No attendance recorded yet.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {[...attendanceList].reverse().map((entry, i) => (
                          <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                            <div>
                              <p className="text-sm font-medium">
                                {entry.student_name || entry.student_id?.slice(0, 8) + '...'}
                              </p>
                              <p className="text-xs text-muted-foreground">{entry.time}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge variant={entry.method === 'face' ? 'success' : 'warning'}>
                                {entry.method?.toUpperCase()}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {((entry.confidence || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Fingerprint Prompt */}
                    {fingerprintNeeded && (
                      <div className="p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                        <div className="flex items-center gap-2 text-orange-500 mb-2">
                          <Fingerprint size={20} />
                          <span className="font-medium text-sm">Fingerprint Verification Needed</span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">
                          A face was detected with 30–69% confidence. Ask the student to place
                          their finger on the sensor, or they can scan directly if not detected.
                        </p>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={handleFingerprintScan}>
                            <Fingerprint className="mr-1 h-3 w-3" />
                            Scan Fingerprint
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => setFingerprintNeeded(false)}>
                            Dismiss
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Direct fingerprint scan option (always available) */}
                    {!fingerprintNeeded && activeSession && (
                      <div className="pt-2 border-t border-border/30">
                        <p className="text-xs text-muted-foreground mb-2">
                          No face detected? Student can scan fingerprint directly:
                        </p>
                        <Button size="sm" variant="outline" onClick={handleFingerprintScan} className="w-full">
                          <Fingerprint className="mr-1 h-3 w-3" />
                          Direct Fingerprint Scan
                        </Button>
                      </div>
                    )}
                  </div>

                ) : (
                  /* ── ROSTER (Sheet) TAB ── */
                  <div className="space-y-2">
                    {!activeSession ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        Start a session to view the attendance sheet.
                      </p>
                    ) : roster.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No students enrolled in this course.
                      </p>
                    ) : (
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b bg-muted/50">
                            <th className="text-left py-2 px-2 font-medium">Student</th>
                            <th className="text-center py-2 px-2 font-medium">Status</th>
                            <th className="text-right py-2 px-2 font-medium">Override</th>
                          </tr>
                        </thead>
                        <tbody>
                          {roster.map((student) => (
                            <tr key={student.student_uuid} className="border-b hover:bg-muted/30">
                              <td className="py-2 px-2">
                                <p className="font-medium">{student.first_name} {student.last_name}</p>
                                <p className="text-xs text-muted-foreground font-mono">{student.student_id}</p>
                              </td>
                              <td className="py-2 px-2 text-center">
                                <Badge variant={
                                  student.status === 'present' ? 'success' :
                                  student.status === 'absent' ? 'destructive' : 'warning'
                                }>
                                  {student.status.toUpperCase()}
                                </Badge>
                              </td>
                              <td className="py-2 px-2 text-right">
                                <select
                                  className="text-xs rounded border border-input bg-background px-1 py-1"
                                  value={student.status}
                                  onChange={(e) => handleManualOverride(student.student_uuid, e.target.value)}
                                >
                                  <option value="absent">Absent</option>
                                  <option value="present">Present</option>
                                  <option value="late">Late</option>
                                  <option value="excused">Excused</option>
                                </select>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
