import React, { useState, useEffect } from 'react';
import { Mail, Settings, CheckCircle, AlertCircle, User } from 'lucide-react';

const EmailConfigSection = ({ API_BASE, isVisible = true }) => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [isConfigured, setIsConfigured] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'

  // Load current email configuration on component mount
  useEffect(() => {
    if (isVisible) {
      loadEmailConfig();
    }
  }, [isVisible]);

  const loadEmailConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/get-user-email`);
      const result = await response.json();

      if (result.success) {
        setEmail(result.email || '');
        setName(result.name || '');
        setIsConfigured(result.configured);
      }
    } catch (error) {
      console.error('Failed to load email configuration:', error);
    }
  };

  const saveEmailConfig = async () => {
    if (!email || !email.includes('@')) {
      setMessage('Please enter a valid email address');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE}/api/set-user-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          name: name.trim() || 'NICL User'
        })
      });

      const result = await response.json();

      if (result.success) {
        setMessage('Email configuration saved successfully!');
        setMessageType('success');
        setIsConfigured(true);
      } else {
        setMessage(result.message || 'Failed to save email configuration');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Failed to save email configuration:', error);
      setMessage('Failed to save email configuration');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200 shadow-sm">
      <div className="flex items-center mb-4">
        <Mail className="text-blue-600 mr-3" size={24} />
        <h3 className="text-xl font-bold text-gray-800">📧 Email Notifications</h3>
      </div>

      <div className="mb-4">
        <p className="text-gray-600 text-sm mb-2">
          Get notified when PDF generation and SMS link creation are completed.
        </p>
        <p className="text-xs text-blue-600">
          💡 Perfect for large files - no need to wait on screen!
        </p>
      </div>

      {/* Status indicator */}
      {isConfigured && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center">
          <CheckCircle className="text-green-600 mr-2" size={16} />
          <span className="text-green-700 text-sm">
            Email notifications are configured for: <strong>{email}</strong>
          </span>
        </div>
      )}

      {/* Configuration form */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <User className="inline mr-1" size={16} />
            Your Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Mail className="inline mr-1" size={16} />
            Email Address *
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <button
          onClick={saveEmailConfig}
          disabled={loading || !email}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-medium flex items-center transition-colors"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Saving...
            </>
          ) : (
            <>
              <Settings className="mr-2" size={16} />
              {isConfigured ? 'Update Configuration' : 'Save Configuration'}
            </>
          )}
        </button>
      </div>

      {/* Status messages */}
      {message && (
        <div className={`mt-4 p-3 rounded-lg flex items-center ${
          messageType === 'success' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          {messageType === 'success' ? (
            <CheckCircle className="text-green-600 mr-2" size={16} />
          ) : (
            <AlertCircle className="text-red-600 mr-2" size={16} />
          )}
          <span className={`text-sm ${
            messageType === 'success' ? 'text-green-700' : 'text-red-700'
          }`}>
            {message}
          </span>
        </div>
      )}

      {/* Information box */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="text-sm font-semibold text-blue-800 mb-2">📬 What You'll Receive:</h4>
        <ul className="text-xs text-blue-700 space-y-1">
          <li>• ✅ PDF Generation completion with summary</li>
          <li>• 📱 SMS Link generation completion with download link</li>
          <li>• ⏱️ Processing time and file counts</li>
          <li>• 🔗 Direct links to access the system</li>
        </ul>
      </div>
    </div>
  );
};

export default EmailConfigSection;