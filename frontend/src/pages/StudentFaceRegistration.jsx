import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { WebcamCapture } from '../components/ui/WebcamCapture';
import { getFaceStatus, uploadFaceImages, deleteFaceData } from '../api/face';
import { useAuth } from '../contexts/AuthContext';
import { ScanFace, Upload, Camera, Trash2 } from 'lucide-react';

export const StudentFaceRegistration = () => {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [enrollMode, setEnrollMode] = useState('upload'); // 'upload' | 'webcam'
  const [faceFiles, setFaceFiles] = useState([]);
  const [webcamBlobs, setWebcamBlobs] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const fetchStatus = async () => {
    try {
      if (user?.profile_id) {
        const data = await getFaceStatus(user.profile_id);
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch face status', err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [user]);

  const handleUploadFaces = async (e) => {
    e.preventDefault();
    const filesToSend = enrollMode === 'webcam' ? webcamBlobs : faceFiles;
    if (!filesToSend || filesToSend.length === 0) return;
    setIsUploading(true);
    try {
      const result = await uploadFaceImages(user.profile_id, filesToSend);
      alert(result.message);
      setFaceFiles([]);
      setWebcamBlobs([]);
      fetchStatus();
    } catch (err) {
      console.error('Failed to upload faces', err);
      alert('Failed to upload face images. Ensure each image contains exactly one visible face.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteFaces = async () => {
    if (confirm('Are you sure you want to delete all your face data? You will need to re-enroll to be marked present automatically.')) {
      try {
        await deleteFaceData(user.profile_id);
        alert('Face data deleted successfully.');
        fetchStatus();
      } catch (err) {
        console.error('Failed to delete face data', err);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Face Registration</h2>
          <p className="text-muted-foreground mt-1">Manage your facial recognition data</p>
        </div>
      </div>

      <Card className="shadow-md">
        <CardHeader className="pb-3 border-b">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ScanFace className="h-5 w-5 text-primary" />
              Enrollment Status
            </div>
            {status?.face_registered ? (
              <span className="text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-3 py-1 rounded-full">
                Registered
              </span>
            ) : (
              <span className="text-xs font-semibold bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 px-3 py-1 rounded-full">
                Not Registered
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex justify-between items-center mb-6">
            <div className="space-y-1">
              <p className="text-sm font-medium">Samples Provided</p>
              <p className="text-2xl font-bold">{status?.total_samples || 0} <span className="text-sm font-normal text-muted-foreground">/ {status?.max_samples || 20}</span></p>
            </div>
            {status?.face_registered && (
              <Button variant="destructive" size="sm" onClick={handleDeleteFaces}>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Data
              </Button>
            )}
          </div>

          <form onSubmit={handleUploadFaces} className="space-y-6">
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Add 5–10 clear, front-facing images for best recognition accuracy. Avoid wearing sunglasses or heavy masks.
              </p>
              
              <div className="flex rounded-lg border border-input overflow-hidden">
                <button
                  type="button"
                  onClick={() => setEnrollMode('upload')}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium transition-colors ${
                    enrollMode === 'upload'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-background text-muted-foreground hover:bg-muted'
                  }`}
                >
                  <Upload className="h-4 w-4" />
                  Upload Files
                </button>
                <button
                  type="button"
                  onClick={() => setEnrollMode('webcam')}
                  className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium transition-colors ${
                    enrollMode === 'webcam'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-background text-muted-foreground hover:bg-muted'
                  }`}
                >
                  <Camera className="h-4 w-4" />
                  Use Webcam
                </button>
              </div>

              {enrollMode === 'upload' && (
                <div className="p-6 border-2 border-dashed rounded-lg bg-muted/20 text-center">
                  <div className="space-y-2">
                    <label className="text-sm font-medium cursor-pointer" htmlFor="face-file-input">
                      <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-3 text-primary">
                        <Upload size={24} />
                      </div>
                      <span className="text-primary hover:underline">Click to browse</span> or drag and drop
                    </label>
                    <input
                      id="face-file-input"
                      type="file"
                      multiple
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => setFaceFiles(Array.from(e.target.files))}
                    />
                    <p className="text-xs text-muted-foreground">Supported formats: JPG, PNG, BMP, WebP</p>
                  </div>
                  {faceFiles.length > 0 && (
                    <div className="mt-4 p-3 bg-background rounded border text-sm text-left">
                      <p className="font-medium mb-1">{faceFiles.length} file{faceFiles.length !== 1 ? 's' : ''} selected</p>
                      <ul className="list-disc pl-5 text-muted-foreground text-xs space-y-1">
                        {faceFiles.map((file, idx) => (
                          <li key={idx} className="truncate">{file.name}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {enrollMode === 'webcam' && (
                <div className="border rounded-lg overflow-hidden bg-muted/10 p-4">
                  <WebcamCapture
                    onCapture={setWebcamBlobs}
                    maxCaptures={status?.max_samples ? status.max_samples - (status.total_samples || 0) : 10}
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end pt-4 border-t">
              <Button
                type="submit"
                disabled={
                  isUploading ||
                  (enrollMode === 'upload' ? faceFiles.length === 0 : webcamBlobs.length === 0) ||
                  (status?.total_samples >= status?.max_samples)
                }
              >
                {isUploading ? 'Uploading…' : 'Upload & Enroll'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
