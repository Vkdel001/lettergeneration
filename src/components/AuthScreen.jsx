import React, { useState } from 'react';
import './AuthScreen.css';

const AuthScreen = ({ onAuthenticated }) => {
  const [authMode, setAuthMode] = useState('email'); // 'email' or 'password'
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [step, setStep] = useState('input'); // 'input', 'otp', 'success'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  // Authorized users
  const authorizedUsers = [
    'sbeekawa@nicl.mu',
    'ncallicharan@nicl.mu', 
    'vikas.khanna@zwennpay.com'
  ];

  // Get API base URL
  const getApiBase = () => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:3001';
    } else {
      return `http://${window.location.hostname}:3001`;
    }
  };

  const API_BASE = getApiBase();

  const validateEmail = (email) => {
    return authorizedUsers.includes(email.toLowerCase().trim());
  };

  const handleEmailAuth = async () => {
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    if (!validateEmail(email)) {
      setError('Access denied. You are not authorized to use this system.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/auth/send-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.toLowerCase().trim() }),
      });

      const result = await response.json();

      if (result.success) {
        setOtpSent(true);
        setStep('otp');
        setError('');
      } else {
        setError(result.message || 'Failed to send OTP. Please try again.');
      }
    } catch (error) {
      console.error('OTP send error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpVerification = async () => {
    if (!otp.trim()) {
      setError('Please enter the OTP');
      return;
    }

    if (otp.length !== 6) {
      setError('OTP must be 6 digits');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/auth/verify-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email: email.toLowerCase().trim(), 
          otp: otp.trim() 
        }),
      });

      const result = await response.json();

      if (result.success) {
        // Store authentication in session
        sessionStorage.setItem('authToken', result.token);
        sessionStorage.setItem('userEmail', email.toLowerCase().trim());
        sessionStorage.setItem('authTime', Date.now().toString());
        
        setStep('success');
        setTimeout(() => {
          onAuthenticated(result.token, email.toLowerCase().trim());
        }, 1000);
      } else {
        setError(result.message || 'Invalid OTP. Please try again.');
      }
    } catch (error) {
      console.error('OTP verification error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordAuth = async () => {
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    if (!validateEmail(email)) {
      setError('Access denied. You are not authorized to use this system.');
      return;
    }

    if (!password.trim()) {
      setError('Please enter the password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/auth/password-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          email: email.toLowerCase().trim(), 
          password: password 
        }),
      });

      const result = await response.json();

      if (result.success) {
        // Store authentication in session
        sessionStorage.setItem('authToken', result.token);
        sessionStorage.setItem('userEmail', email.toLowerCase().trim());
        sessionStorage.setItem('authTime', Date.now().toString());
        
        setStep('success');
        setTimeout(() => {
          onAuthenticated(result.token, email.toLowerCase().trim());
        }, 1000);
      } else {
        setError(result.message || 'Invalid credentials. Please try again.');
      }
    } catch (error) {
      console.error('Password auth error:', error);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setOtp('');
    setError('');
    await handleEmailAuth();
  };

  const resetForm = () => {
    setEmail('');
    setOtp('');
    setPassword('');
    setStep('input');
    setError('');
    setOtpSent(false);
    setLoading(false);
  };

  return (
    <div className="auth-screen">
      <div className="auth-container">
        <div className="auth-header">
          <img src="/nic-logo.png" alt="NIC Insurance" className="auth-logo" />
          <h1>NIC PDF Generator</h1>
          <p>Secure Access Required</p>
        </div>

        {step === 'input' && (
          <div className="auth-form">
            <div className="auth-mode-selector">
              <button 
                className={`mode-btn ${authMode === 'email' ? 'active' : ''}`}
                onClick={() => setAuthMode('email')}
              >
                Email + OTP
              </button>
              <button 
                className={`mode-btn ${authMode === 'password' ? 'active' : ''}`}
                onClick={() => setAuthMode('password')}
              >
                Password
              </button>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your authorized email"
                disabled={loading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    if (authMode === 'email') {
                      handleEmailAuth();
                    } else {
                      document.getElementById('password').focus();
                    }
                  }
                }}
              />
            </div>

            {authMode === 'password' && (
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  disabled={loading}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handlePasswordAuth();
                    }
                  }}
                />
              </div>
            )}

            {error && <div className="error-message">{error}</div>}

            <button 
              className="auth-btn primary"
              onClick={authMode === 'email' ? handleEmailAuth : handlePasswordAuth}
              disabled={loading}
            >
              {loading ? 'Processing...' : (authMode === 'email' ? 'Send OTP' : 'Login')}
            </button>


          </div>
        )}

        {step === 'otp' && (
          <div className="auth-form">
            <div className="otp-step">
              <h3>Enter OTP</h3>
              <p>We've sent a 6-digit code to <strong>{email}</strong></p>
              
              <div className="form-group">
                <label htmlFor="otp">OTP Code</label>
                <input
                  type="text"
                  id="otp"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="Enter 6-digit OTP"
                  disabled={loading}
                  maxLength="6"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleOtpVerification();
                    }
                  }}
                />
              </div>

              {error && <div className="error-message">{error}</div>}

              <button 
                className="auth-btn primary"
                onClick={handleOtpVerification}
                disabled={loading || otp.length !== 6}
              >
                {loading ? 'Verifying...' : 'Verify OTP'}
              </button>

              <div className="otp-actions">
                <button 
                  className="auth-btn secondary"
                  onClick={handleResendOtp}
                  disabled={loading}
                >
                  Resend OTP
                </button>
                <button 
                  className="auth-btn secondary"
                  onClick={resetForm}
                  disabled={loading}
                >
                  Back
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div className="auth-form">
            <div className="success-step">
              <div className="success-icon">✅</div>
              <h3>Authentication Successful</h3>
              <p>Welcome, {email}</p>
              <p>Redirecting to PDF Generator...</p>
            </div>
          </div>
        )}

        <div className="auth-footer">
          <p>© 2025 NIC Insurance - Secure PDF Generation System</p>
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;