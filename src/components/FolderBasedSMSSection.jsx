import React, { useState, useEffect } from 'react';
import { MessageSquare, Download, Loader, CheckCircle, AlertCircle, Folder, Calendar, FileText, Smartphone } from 'lucide-react';

const FolderBasedSMSSection = ({ API_BASE, isVisible = true }) => {
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Load available folders on component mount
  useEffect(() => {
    if (isVisible) {
      loadFolders();
    }
  }, [isVisible]);

  const loadFolders = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log('[FOLDER-SMS] Loading available PDF folders...');
      const response = await fetch(`${API_BASE}/api/pdf-folders-enhanced`);
      const result = await response.json();

      if (result.success) {
        setFolders(result.folders);
        console.log(`[FOLDER-SMS] Loaded ${result.folders.length} folders`);
      } else {
        throw new Error(result.message || 'Failed to load folders');
      }
    } catch (error) {
      console.error('[FOLDER-SMS] Error loading folders:', error);
      setError(`Failed to load folders: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateSMSLinksFromFolder = async (folder) => {
    setIsGenerating(true);
    setError('');
    setSuccess('');
    setSelectedFolder(folder);

    try {
      console.log('[FOLDER-SMS] Starting SMS link generation for folder:', folder.name);

      const response = await fetch(`${API_BASE}/api/generate-sms-links-from-folder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          folderName: folder.name,
          template: folder.template,
          baseUrl: API_BASE  // Use the API_BASE which is correctly set to localhost:3001
        })
      });

      const result = await response.json();
      console.log('[FOLDER-SMS] Server response:', result);

      if (result.success) {
        setSuccess(`Successfully generated ${result.linksGenerated} SMS links for ${folder.name}!`);
        
        // Add a small delay to ensure file system has updated timestamps
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Refresh folder list to update SMS status
        await loadFolders();
      } else {
        throw new Error(result.message || 'Failed to generate SMS links');
      }

    } catch (error) {
      console.error('[FOLDER-SMS] Error:', error);
      setError(`Failed to generate SMS links: ${error.message}`);
    } finally {
      setIsGenerating(false);
      setSelectedFolder(null);
    }
  };

  const downloadSMSFile = (folder) => {
    try {
      const downloadUrl = `${API_BASE}/api/download-sms-file/${folder.name}`;
      console.log('[FOLDER-SMS] Downloading SMS file from:', downloadUrl);
      
      // Create a temporary link to trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `SMS_Batch_${folder.name}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      setSuccess(`SMS file download started for ${folder.name}!`);
    } catch (error) {
      console.error('[FOLDER-SMS] Download error:', error);
      setError('Failed to download SMS file');
    }
  };

  const getStatusIcon = (folder) => {
    if (folder.smsLinksGenerated && folder.smsLinksUpToDate) {
      return <Smartphone className="text-blue-600" size={20} />;
    } else if (folder.smsLinksCount > 0 && !folder.smsLinksUpToDate) {
      return <AlertCircle className="text-orange-600" size={20} />;
    } else if (folder.status === 'complete') {
      return <CheckCircle className="text-green-600" size={20} />;
    } else if (folder.status === 'partial') {
      return <AlertCircle className="text-yellow-600" size={20} />;
    } else {
      return <Folder className="text-gray-600" size={20} />;
    }
  };

  const getStatusText = (folder) => {
    if (folder.smsLinksGenerated && folder.smsLinksUpToDate) {
      return `SMS Ready (${folder.smsLinksCount} links)`;
    } else if (folder.smsLinksCount > 0 && !folder.smsLinksUpToDate) {
      return `SMS Outdated (${folder.smsLinksCount}/${folder.pdfCount})`;
    } else if (folder.status === 'complete') {
      return 'Ready for SMS';
    } else if (folder.status === 'partial') {
      return 'Partial PDFs';
    } else {
      return 'Unknown Status';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 shadow-sm">
      <div className="flex items-center mb-4">
        <Folder className="text-purple-600 mr-3" size={24} />
        <h3 className="text-xl font-bold text-gray-800">📁 Folder-Based SMS Link Generation</h3>
      </div>

      <div className="mb-4">
        <p className="text-gray-600 text-sm mb-2">
          Generate SMS links from any existing PDF folder - no need to wait during PDF generation!
        </p>
        <p className="text-xs text-purple-600">
          💡 Select any folder below to create SMS links independently of current PDF generation.
        </p>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
          <AlertCircle className="text-red-600 mr-2" size={16} />
          <span className="text-red-700 text-sm">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center">
          <CheckCircle className="text-green-600 mr-2" size={16} />
          <span className="text-green-700 text-sm">{success}</span>
        </div>
      )}

      {/* Refresh Button */}
      <div className="mb-4">
        <button
          onClick={loadFolders}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium flex items-center transition-colors"
        >
          {loading ? (
            <>
              <Loader className="animate-spin mr-2" size={16} />
              Loading Folders...
            </>
          ) : (
            <>
              <Folder className="mr-2" size={16} />
              Refresh Folders
            </>
          )}
        </button>
      </div>

      {/* Folder List */}
      {folders.length > 0 ? (
        <div className="space-y-3">
          <h4 className="font-semibold text-gray-700 mb-3">Available PDF Folders ({folders.length}):</h4>
          
          {folders.map((folder, index) => (
            <div
              key={folder.name}
              className={`bg-white rounded-lg border-2 p-4 transition-all duration-200 ${
                selectedFolder?.name === folder.name && isGenerating
                  ? 'border-blue-400 bg-blue-50'
                  : folder.smsLinksGenerated
                  ? 'border-green-200 hover:border-green-300'
                  : 'border-gray-200 hover:border-purple-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    {getStatusIcon(folder)}
                    <span className="font-semibold text-gray-800 ml-2">
                      {folder.name}
                      {index === 0 && (
                        <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          Latest
                        </span>
                      )}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm text-gray-600 mb-3">
                    <div className="flex items-center">
                      <FileText size={14} className="mr-1" />
                      <span>{folder.pdfCount} PDFs</span>
                    </div>
                    <div className="flex items-center">
                      <Calendar size={14} className="mr-1" />
                      <span>{formatDate(folder.lastModified)}</span>
                    </div>
                    <div>
                      <span className="font-medium">Template:</span> {folder.templateType}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span> {getStatusText(folder)}
                    </div>
                  </div>

                  {!folder.hasFolderSpecificExcel && (
                    <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                      ❌ No folder-specific Excel file found - SMS generation not available
                    </div>
                  )}

                  {!folder.hasExcelFile && folder.hasFolderSpecificExcel && (
                    <div className="mb-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
                      ⚠️ Excel file not found - SMS generation may fail
                    </div>
                  )}

                  {folder.smsLinksCount > 0 && !folder.smsLinksUpToDate && (
                    <div className="mb-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs text-orange-700">
                      🔄 SMS links are outdated ({folder.smsLinksCount} links for {folder.pdfCount} PDFs) - regenerate recommended
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 ml-4">
                  {folder.smsLinksGenerated && folder.smsLinksUpToDate ? (
                    // SMS links are up-to-date, show download button
                    <button
                      onClick={() => downloadSMSFile(folder)}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium flex items-center transition-colors"
                    >
                      <Download className="mr-2" size={16} />
                      Download SMS
                    </button>
                  ) : (
                    // No SMS links or outdated SMS links, show generate button
                    <button
                      onClick={() => generateSMSLinksFromFolder(folder)}
                      disabled={isGenerating || folder.status !== 'complete' || !folder.hasFolderSpecificExcel}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium flex items-center transition-colors"
                    >
                      {selectedFolder?.name === folder.name && isGenerating ? (
                        <>
                          <Loader className="animate-spin mr-2" size={16} />
                          Generating...
                        </>
                      ) : (
                        <>
                          <MessageSquare className="mr-2" size={16} />
                          {folder.smsLinksCount > 0 ? 'Regenerate SMS' : 'Generate SMS'}
                        </>
                      )}
                    </button>
                  )}
                  
                  {/* Show download button for outdated SMS links as secondary option */}
                  {folder.smsLinksCount > 0 && !folder.smsLinksUpToDate && (
                    <button
                      onClick={() => downloadSMSFile(folder)}
                      className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm flex items-center transition-colors"
                    >
                      <Download className="mr-1" size={14} />
                      Download Old SMS
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : loading ? (
        <div className="text-center py-8">
          <Loader className="animate-spin mx-auto mb-4 text-purple-600" size={32} />
          <p className="text-gray-600">Loading PDF folders...</p>
        </div>
      ) : (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <Folder className="mx-auto mb-4 text-gray-400" size={48} />
          <p className="text-gray-600 mb-2">No PDF folders found</p>
          <p className="text-sm text-gray-500">Generate some PDFs first, then refresh to see available folders.</p>
        </div>
      )}

      {/* Information Box */}
      <div className="mt-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
        <h4 className="text-sm font-semibold text-purple-800 mb-2">How Folder-Based SMS Generation Works:</h4>
        <ul className="text-xs text-purple-700 space-y-1">
          <li>• Select any existing PDF folder to generate SMS links</li>
          <li>• Template is auto-detected from folder name</li>
          <li>• Works independently of current PDF generation</li>
          <li>• Can process folders created hours or days ago</li>
          <li>• SMS links expire after 30 days for security</li>
        </ul>
      </div>
    </div>
  );
};

export default FolderBasedSMSSection;