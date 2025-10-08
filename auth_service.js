import crypto from 'crypto';
import jwt from 'jsonwebtoken';
// Note: We'll use a direct approach for Brevo API calls instead of importing Python config

// In-memory storage for OTPs (in production, use Redis or database)
const otpStore = new Map();
const sessionStore = new Map();

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'NIC_PDF_GENERATOR_SECRET_2025';
const OTP_EXPIRY = 10 * 60 * 1000; // 10 minutes
const SESSION_EXPIRY = 8 * 60 * 60 * 1000; // 8 hours

// Authorized users
const AUTHORIZED_USERS = [
  'sbeekawa@nicl.mu',
  'ncallicharan@nicl.mu', 
  'vikas.khanna@zwennpay.com'
];

// Master password
const MASTER_PASSWORD = 'NICLAR@2025';

class AuthService {
  
  // Generate 6-digit OTP
  static generateOTP() {
    return Math.floor(100000 + Math.random() * 900000).toString();
  }

  // Generate JWT token
  static generateToken(email) {
    return jwt.sign(
      { 
        email, 
        iat: Date.now(),
        exp: Date.now() + SESSION_EXPIRY 
      },
      JWT_SECRET
    );
  }

  // Verify JWT token
  static verifyToken(token) {
    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      
      // Check if token is expired
      if (decoded.exp < Date.now()) {
        return { valid: false, error: 'Token expired' };
      }

      // Check if user is still authorized
      if (!AUTHORIZED_USERS.includes(decoded.email)) {
        return { valid: false, error: 'User no longer authorized' };
      }

      return { valid: true, email: decoded.email };
    } catch (error) {
      return { valid: false, error: 'Invalid token' };
    }
  }

  // Check if email is authorized
  static isAuthorizedUser(email) {
    return AUTHORIZED_USERS.includes(email.toLowerCase().trim());
  }

  // Send OTP via existing Brevo service
  static async sendOTP(email) {
    try {
      if (!this.isAuthorizedUser(email)) {
        return {
          success: false,
          message: 'Access denied. You are not authorized to use this system.'
        };
      }

      const otp = this.generateOTP();
      const otpKey = email.toLowerCase().trim();
      
      // Store OTP with expiry
      otpStore.set(otpKey, {
        otp,
        createdAt: Date.now(),
        attempts: 0
      });

      // Clean up expired OTPs
      this.cleanupExpiredOTPs();

      // Use existing Brevo service by calling the Python script
      const { spawn } = await import('child_process');
      
      // Create temporary email data for OTP
      const otpEmailData = [{
        email: email,
        name: 'NIC User',
        subject: 'NIC PDF Generator - Access Code',
        otp: otp
      }];

      // Create temp file for OTP email data
      const fs = await import('fs');
      const path = await import('path');
      const tempFile = path.resolve('.', `temp_otp_${Date.now()}.json`);
      
      try {
        fs.writeFileSync(tempFile, JSON.stringify(otpEmailData));
        
        // Call the existing Brevo service with OTP-specific parameters
        const python = spawn('python', [
          'send_otp_email.py',  // We'll create this specialized script
          '--email', email,
          '--otp', otp
        ]);

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        return new Promise((resolve) => {
          python.on('close', (code) => {
            // Clean up temp file
            try {
              if (fs.existsSync(tempFile)) {
                fs.unlinkSync(tempFile);
              }
            } catch (e) {
              console.warn('Could not clean up temp OTP file');
            }

            if (code === 0) {
              console.log(`[AUTH] OTP sent successfully to ${email}`);
              resolve({
                success: true,
                message: 'OTP sent successfully to your email address'
              });
            } else {
              console.error(`[AUTH] Failed to send OTP to ${email}:`, stderr);
              resolve({
                success: false,
                message: 'Failed to send OTP. Please try again or contact support.'
              });
            }
          });

          python.on('error', (error) => {
            console.error('[AUTH] Error calling OTP service:', error);
            resolve({
              success: false,
              message: 'System error. Please try again later.'
            });
          });
        });

      } catch (fileError) {
        console.error('[AUTH] Error creating temp file:', fileError);
        return {
          success: false,
          message: 'System error. Please try again later.'
        };
      }

    } catch (error) {
      console.error('[AUTH] Error sending OTP:', error);
      return {
        success: false,
        message: 'System error. Please try again later.'
      };
    }
  }

  // Verify OTP
  static verifyOTP(email, inputOtp) {
    try {
      const otpKey = email.toLowerCase().trim();
      const storedData = otpStore.get(otpKey);

      if (!storedData) {
        return {
          success: false,
          message: 'No OTP found. Please request a new one.'
        };
      }

      // Check if OTP is expired
      if (Date.now() - storedData.createdAt > OTP_EXPIRY) {
        otpStore.delete(otpKey);
        return {
          success: false,
          message: 'OTP has expired. Please request a new one.'
        };
      }

      // Check attempt limit
      if (storedData.attempts >= 3) {
        otpStore.delete(otpKey);
        return {
          success: false,
          message: 'Too many failed attempts. Please request a new OTP.'
        };
      }

      // Verify OTP
      if (storedData.otp === inputOtp.trim()) {
        // OTP is correct
        otpStore.delete(otpKey); // Remove used OTP
        
        const token = this.generateToken(email);
        
        // Store session
        sessionStore.set(token, {
          email,
          createdAt: Date.now(),
          lastActivity: Date.now()
        });

        console.log(`[AUTH] Successful OTP authentication for ${email}`);
        
        return {
          success: true,
          token,
          message: 'Authentication successful'
        };
      } else {
        // Increment attempt counter
        storedData.attempts++;
        otpStore.set(otpKey, storedData);
        
        return {
          success: false,
          message: `Invalid OTP. ${3 - storedData.attempts} attempts remaining.`
        };
      }

    } catch (error) {
      console.error('[AUTH] Error verifying OTP:', error);
      return {
        success: false,
        message: 'System error. Please try again.'
      };
    }
  }

  // Password authentication
  static passwordAuth(email, password) {
    try {
      if (!this.isAuthorizedUser(email)) {
        return {
          success: false,
          message: 'Access denied. You are not authorized to use this system.'
        };
      }

      if (password === MASTER_PASSWORD) {
        const token = this.generateToken(email);
        
        // Store session
        sessionStore.set(token, {
          email,
          createdAt: Date.now(),
          lastActivity: Date.now()
        });

        console.log(`[AUTH] Successful password authentication for ${email}`);
        
        return {
          success: true,
          token,
          message: 'Authentication successful'
        };
      } else {
        console.log(`[AUTH] Failed password authentication for ${email}`);
        return {
          success: false,
          message: 'Invalid password'
        };
      }

    } catch (error) {
      console.error('[AUTH] Error in password authentication:', error);
      return {
        success: false,
        message: 'System error. Please try again.'
      };
    }
  }

  // Middleware to check authentication
  static authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Access denied. No authentication token provided.'
      });
    }

    const verification = AuthService.verifyToken(token);
    
    if (!verification.valid) {
      return res.status(401).json({
        success: false,
        message: verification.error || 'Invalid authentication token'
      });
    }

    // Update last activity
    const session = sessionStore.get(token);
    if (session) {
      session.lastActivity = Date.now();
      sessionStore.set(token, session);
    }

    req.user = { email: verification.email };
    next();
  }

  // Clean up expired OTPs and sessions
  static cleanupExpiredOTPs() {
    const now = Date.now();
    
    // Clean expired OTPs
    for (const [key, data] of otpStore.entries()) {
      if (now - data.createdAt > OTP_EXPIRY) {
        otpStore.delete(key);
      }
    }

    // Clean expired sessions
    for (const [token, session] of sessionStore.entries()) {
      if (now - session.lastActivity > SESSION_EXPIRY) {
        sessionStore.delete(token);
      }
    }
  }

  // Get active sessions (for monitoring)
  static getActiveSessions() {
    this.cleanupExpiredOTPs();
    return Array.from(sessionStore.values()).map(session => ({
      email: session.email,
      createdAt: new Date(session.createdAt).toISOString(),
      lastActivity: new Date(session.lastActivity).toISOString()
    }));
  }
}

// Clean up expired data every 5 minutes
setInterval(() => {
  AuthService.cleanupExpiredOTPs();
}, 5 * 60 * 1000);

export default AuthService;