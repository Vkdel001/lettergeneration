import React, { useState, useEffect } from 'react';
import { Folder, FileText, Download, RefreshCw, Calendar, HardDrive } from 'lucide-react';

const FileBrowser = ({ onDownload, API_BASE }) => {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [expandedFolders, setExpandedFolders] = useState(new Set());

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const fetchCombinedFiles = async () => {
    setLoading(true);
    try {
      // Get all folders
      const foldersResponse = await fetch(`${API_BASE}/api/folders`);
      const foldersData = await foldersResponse.json();
      
      if (foldersData.success) {
        const foldersWithCombined = [];
        
        for (const folder of foldersData.folders) {
          // Check if this folder has combined files
          try {
            const combinedPath = `${folder.name}/combined`;
            const combinedResponse = await fetch(`${API_BASE}/api/folder-contents/${folder.name}/combined`);
            
            if (combinedResponse.ok) {
              const combinedData = await combinedResponse.json();
              if (combinedData.success && combinedData.files.length > 0) {
                foldersWithCombined.push({
                  ...folder,
                  combinedFiles: combinedData.files,
                  hasCombined: true
                });
              }
            }
          } catch (error) {
            // Folder might not have combined files, skip
            console.log(`No combined files in ${folder.name}`);
          }
        }
        
        setFolders(foldersWithCombined);
      }
    } catch (error) {
      console.error('Error fetching combined files:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCombinedFiles();
  }, [API_BASE]);

  const toggleFolder = (folderName) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderName)) {
      newExpanded.delete(folderName);
    } else {
      newExpanded.add(folderName);
    }
    setExpandedFolders(newExpanded);
  };

  const toggleFileSelection = (filePath) => {
    setSelectedFiles(prev => {
      if (prev.includes(filePath)) {
        return prev.filter(f => f !== filePath);
      } else {
        return [...prev, filePath];
      }
    });
  };

  const handleDownloadSelected = () => {
    if (selectedFiles.length === 0) return;
    
    selectedFiles.forEach((filePath, index) => {
      setTimeout(() => {
        onDownload(filePath);
      }, index * 500); // Stagger downloads
    });
    
    setSelectedFiles([]);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <RefreshCw className="animate-spin text-blue-600 mr-3" size={24} />
          <span className="text-gray-600">Loading combined files...</span>
        </div>
      </div>
    );
  }

  if (folders.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <Folder className="mx-auto text-gray-400 mb-4" size={48} />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">No Combined Files Found</h3>
        <p className="text-gray-500 mb-4">
          No combined PDF files are available for download. 
          Use the "Combine PDFs" tab to create combined files first.
        </p>
        <button
          onClick={fetchCombinedFiles}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw size={16} className="mr-2" />
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-gray-800">Combined PDF Files</h3>
        <div className="flex items-center space-x-3">
          {selectedFiles.length > 0 && (
            <span className="text-sm text-blue-600 font-medium">
              {selectedFiles.length} selected
            </span>
          )}
          <button
            onClick={fetchCombinedFiles}
            className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            title="Refresh"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {folders.map((folder) => (
          <div key={folder.name} className="border border-gray-200 rounded-lg">
            <button
              onClick={() => toggleFolder(folder.name)}
              className="w-full flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-gray-50 transition-colors space-y-2 sm:space-y-0"
            >
              <div className="flex items-center">
                <Folder className="text-blue-600 mr-3" size={20} />
                <div className="text-left">
                  <h4 className="font-semibold text-gray-800">{folder.name}</h4>
                  <p className="text-sm text-gray-500">
                    {folder.combinedFiles?.length || 0} combined files
                  </p>
                </div>
              </div>
              <div className="text-left sm:text-right text-sm text-gray-500">
                <p>{folder.pdfCount} original PDFs</p>
                <p className="text-xs">Click to expand</p>
              </div>
            </button>

            {expandedFolders.has(folder.name) && folder.combinedFiles && (
              <div className="border-t border-gray-200 bg-gray-50">
                {folder.combinedFiles.map((file) => (
                  <div
                    key={file.path}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-white transition-colors space-y-3 sm:space-y-0"
                  >
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedFiles.includes(file.path)}
                        onChange={() => toggleFileSelection(file.path)}
                        className="mr-3 w-4 h-4 text-blue-600"
                      />
                      <FileText className="text-red-600 mr-3 flex-shrink-0" size={16} />
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-gray-800 truncate">{file.filename}</p>
                        <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 text-xs text-gray-500 space-y-1 sm:space-y-0">
                          <span className="flex items-center">
                            <HardDrive size={12} className="mr-1" />
                            {formatBytes(file.size)}
                          </span>
                          <span className="flex items-center">
                            <Calendar size={12} className="mr-1" />
                            {formatDate(file.lastModified)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => onDownload(file.filename)}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors whitespace-nowrap"
                    >
                      Download
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedFiles.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-3 sm:space-y-0">
            <span className="text-blue-800 font-medium">
              {selectedFiles.length} files selected
            </span>
            <div className="flex space-x-3">
              <button
                onClick={() => setSelectedFiles([])}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                Clear
              </button>
              <button
                onClick={handleDownloadSelected}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Download Selected
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileBrowser;