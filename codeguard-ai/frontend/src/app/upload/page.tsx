'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, Loader2 } from 'lucide-react';
import { FileUpload } from '@/components/ui/file-upload';
import { uploadService } from '@/lib/upload-service';
import { authService } from '@/lib/auth-service';

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  const handleScan = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError('');
    try {
      const scan = await uploadService.uploadAndScan({
        files,
        projectName: projectName.trim() || undefined,
      });
      router.push(`/results/${scan.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload scan failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-8">
          <h1 className="text-3xl font-bold text-white">Upload & Scan</h1>
          <p className="mt-2 text-slate-400">
            Drop source files for instant security analysis, no repository required.
          </p>
        </header>

        <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
          <input
            type="text"
            placeholder="Project name (optional)"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="mb-6 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/60"
          />

          <FileUpload onFilesSelected={setFiles} maxFiles={50} maxSize={10} />

          {error && (
            <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-red-100">
              {error}
            </div>
          )}

          <button
            onClick={handleScan}
            disabled={loading || files.length === 0}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-6 py-4 font-semibold text-cyan-100 transition hover:bg-cyan-300/15 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <Upload size={20} />
                <span>
                  Scan {files.length} file{files.length !== 1 ? 's' : ''}
                </span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
