'use client';

import React, { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  maxSize?: number; // in MB
}

export function FileUpload({ 
  onFilesSelected, 
  maxFiles = 10, 
  acceptedTypes = ['.js', '.ts', '.py', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs'],
  maxSize = 10 
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [errors, setErrors] = useState<string[]>([]);

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > maxSize * 1024 * 1024) {
      return `File ${file.name} is too large (max ${maxSize}MB)`;
    }

    // Check file type
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (acceptedTypes.length > 0 && !acceptedTypes.includes(extension)) {
      return `File type ${extension} is not supported`;
    }

    return null;
  }, [acceptedTypes, maxSize]);

  const handleFiles = useCallback((files: FileList) => {
    const newFiles: File[] = [];
    const newErrors: string[] = [];

    Array.from(files).forEach(file => {
      const error = validateFile(file);
      if (error) {
        newErrors.push(error);
      } else if (selectedFiles.length + newFiles.length < maxFiles) {
        newFiles.push(file);
      } else {
        newErrors.push(`Maximum ${maxFiles} files allowed`);
      }
    });

    if (newFiles.length > 0) {
      const updatedFiles = [...selectedFiles, ...newFiles];
      setSelectedFiles(updatedFiles);
      onFilesSelected(updatedFiles);
    }

    setErrors(newErrors);
  }, [maxFiles, onFilesSelected, selectedFiles, validateFile]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (index: number) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(updatedFiles);
    onFilesSelected(updatedFiles);
  };

  const clearErrors = () => setErrors([]);

  return (
    <div className="w-full">
      {/* Upload Area */}
      <div
        className={`relative rounded-3xl border-2 border-dashed p-8 text-center transition-colors ${
          dragActive
            ? 'border-cyan-300/60 bg-cyan-300/10'
            : 'border-white/15 bg-slate-950/50 hover:border-white/25'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          onChange={handleChange}
          accept={acceptedTypes.join(',')}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <Upload className="mx-auto mb-4 h-12 w-12 text-cyan-200" />
        <p className="mb-2 text-lg font-medium text-slate-200">
          Drop your code files here, or click to browse
        </p>
        <p className="text-sm text-slate-500">
          Supports: {acceptedTypes.join(', ')} (max {maxSize}MB each, {maxFiles} files total)
        </p>
      </div>

      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <AlertCircle className="text-red-400" size={20} />
              <span className="font-medium text-red-200">Upload Errors</span>
            </div>
            <button
              onClick={clearErrors}
              className="text-red-400 hover:text-red-300"
            >
              <X size={16} />
            </button>
          </div>
          <ul className="space-y-1 text-sm text-red-200">
            {errors.map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-3 flex items-center gap-2 text-lg font-medium text-slate-200">
            <CheckCircle className="text-emerald-300" size={20} />
            <span>Selected Files ({selectedFiles.length})</span>
          </h3>
          <div className="space-y-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/60 p-3"
              >
                <div className="flex items-center space-x-3">
                  <File className="text-cyan-200" size={20} />
                  <div>
                    <p className="text-white font-medium">{file.name}</p>
                    <p className="text-sm text-slate-400">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-slate-400 transition hover:text-red-300"
                >
                  <X size={20} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
