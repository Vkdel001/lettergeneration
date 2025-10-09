import React, { useState, useEffect } from 'react';
import { Download, X, Pause, Play, AlertCircle } from 'lucide-react';

const DownloadProgress = ({ 
  isVisible, 
  onClose, 
  filename, 
  fileSize, 
  estimatedTime,
  onConfirm,
  onCancel 
}) => {
  const [progress, setProgress] = useState(0);
  const [downloadSpeed, setDownloadSpeed] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(estimatedTime);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [downloadedBytes, setDownloadedBytes] = useState(0);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatTime = (seconds) => {
    if (seconds < 60) return `${Math.ceil(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${Math.ceil(remainingSeconds)}s`;
  };

  const formatSpeed = (bytesPerSecond) => {
    return `${formatBytes(bytesPerSecond)}/s`;
  };

  const handleDownloadWithProgress = async () => {
    setIsDownloading(true);
    setProgress(0);
    
    try {
      const startTime = Date.now();
      let lastLoaded = 0;
      
      // Simulate progress for demonstration
      // In real implementation, this would use fetch with ReadableStream
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            setIsDownloading(false);
            onConfirm(); // Trigger actual download
            return 100;
          }
          
          const newProgress = prev + Math.random() * 5;
          const currentTime = Date.now();
          const elapsedSeconds = (currentTime - startTime) / 1000;
          const currentBytes = (newProgress / 100) * fileSize;
          const speed = elapsedSeconds > 0 ? (currentBytes - lastLoaded) / elapsedSeconds : 0;
          
          setDownloadedBytes(currentBytes);
          setDownloadSpeed(speed);
          setTimeRemaining(speed > 0 ? (fileSize - currentBytes) / speed : 0);
          
          lastLoaded = currentBytes;
          return Math.min(newProgress, 100);
        });
      }, 200);
      
    } catch (error) {
      console.error('Download error:', error);
      setIsDownloading(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl p-4 sm:p-8 max-w-md w-full max-h-screen overflow-y-auto">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center">
            <Download className="text-blue-600 mr-3" size={24} />
            <h3 className="text-xl font-bold text-gray-800">
              {isDownloading ? 'Downloading' : 'Download File'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {!isDownloading ? (
          // Pre-download info
          <div className="space-y-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-800 mb-2">📁 {filename}</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>File Size:</span>
                  <span className="font-medium">{formatBytes(fileSize)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Estimated Time:</span>
                  <span className="font-medium">{estimatedTime}</span>
                </div>
                <div className="flex justify-between">
                  <span>Connection:</span>
                  <span className="font-medium text-green-600">Stable</span>
                </div>
              </div>
            </div>

            {fileSize > 100 * 1024 * 1024 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="text-amber-600 mr-3 mt-0.5 flex-shrink-0" size={16} />
                <div className="text-sm text-amber-800">
                  <p className="font-medium mb-1">Large File Warning</p>
                  <p>This file is over 100MB. Ensure you have a stable internet connection.</p>
                </div>
              </div>
            )}

            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 pt-4">
              <button
                onClick={handleDownloadWithProgress}
                className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Start Download
              </button>
              <button
                onClick={onCancel}
                className="px-4 py-3 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          // Download progress
          <div className="space-y-4">
            <div className="text-center">
              <p className="text-gray-600 mb-2">📥 Downloading {filename}</p>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-2xl font-bold text-blue-600 mb-2">{Math.round(progress)}%</p>
              <p className="text-sm text-gray-600">
                {formatBytes(downloadedBytes)} / {formatBytes(fileSize)}
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Speed:</span>
                <span className="font-medium">{formatSpeed(downloadSpeed)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Time Remaining:</span>
                <span className="font-medium">{formatTime(timeRemaining)}</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <button
                onClick={() => setIsPaused(!isPaused)}
                className="flex items-center justify-center px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                {isPaused ? <Play size={16} className="mr-2" /> : <Pause size={16} className="mr-2" />}
                {isPaused ? 'Resume' : 'Pause'}
              </button>
              <button
                onClick={onCancel}
                className="px-4 py-2 text-red-600 hover:text-red-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DownloadProgress;