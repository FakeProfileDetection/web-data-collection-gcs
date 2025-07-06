// cloud-functions/saver/index.js

const { Storage } = require('@google-cloud/storage');
const busboy = require('busboy');
const crypto = require('crypto');

/* ------------------------------------------------------------------ */
/* 1. Configuration and Constants                                     */
/* ------------------------------------------------------------------ */
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB limit
const ALLOWED_MIME_TYPES = [
  'application/json',
  'text/csv',
  'text/plain'
];

const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX_REQUESTS = 30; // max requests per window

// Initialize Cloud Storage
const storage = new Storage();
const BUCKET_NAME = 'fake-profile-detection-eda-bucket';
const UPLOAD_PREFIX = 'uploads/';

// Rate limiting storage (in production, use Memorystore/Redis)
const rateLimitStore = new Map();

/* ------------------------------------------------------------------ */
/* 2. CORS Headers Configuration                                      */
/* ------------------------------------------------------------------ */
const corsHeaders = {
  /*'Access-Control-Allow-Origin': 'https://fakeprofiledetection.github.io',*/
    'Access-Control-Allow-Origin': '*', // For development, restrict in production
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '3600',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
};

/* ------------------------------------------------------------------ */
/* 3. Security and validation utilities                              */
/* ------------------------------------------------------------------ */

/**
 * Rate limiting implementation
 */
function checkRateLimit(clientIP) {
  const now = Date.now();
  const windowStart = now - RATE_LIMIT_WINDOW;
  
  // Clean old entries
  for (const [ip, requests] of rateLimitStore.entries()) {
    const filteredRequests = requests.filter(time => time > windowStart);
    if (filteredRequests.length === 0) {
      rateLimitStore.delete(ip);
    } else {
      rateLimitStore.set(ip, filteredRequests);
    }
  }
  
  // Check current IP
  const requests = rateLimitStore.get(clientIP) || [];
  const recentRequests = requests.filter(time => time > windowStart);
  
  if (recentRequests.length >= RATE_LIMIT_MAX_REQUESTS) {
    return false;
  }
  
  // Add current request
  recentRequests.push(now);
  rateLimitStore.set(clientIP, recentRequests);
  
  return true;
}

/**
 * Validate file content and metadata
 */
function validateFile(fileName, fileBuffer, contentType) {
  const errors = [];
  
  // File size validation
  if (fileBuffer.length > MAX_FILE_SIZE) {
    errors.push(`File size exceeds limit of ${MAX_FILE_SIZE / 1024 / 1024}MB`);
  }
  
  // File name validation
  if (!fileName || fileName.length > 255) {
    errors.push('Invalid file name');
  }
  
  // File name sanitization check
  const sanitizedName = fileName.replace(/[^a-zA-Z0-9._-]/g, '');
  if (sanitizedName !== fileName) {
    errors.push('File name contains invalid characters');
  }
  
  // MIME type validation
  if (!ALLOWED_MIME_TYPES.includes(contentType)) {
    errors.push(`File type not allowed. Allowed types: ${ALLOWED_MIME_TYPES.join(', ')}`);
  }
  
  // Content validation for JSON files
  if (contentType === 'application/json') {
    try {
      JSON.parse(fileBuffer.toString());
    } catch (e) {
      errors.push('Invalid JSON content');
    }
  }
  
  // Check for suspicious content patterns
  const fileContent = fileBuffer.toString().toLowerCase();
  const suspiciousPatterns = [
    '<script',
    'javascript:',
    'data:text/html',
    'eval(',
    'document.cookie'
  ];
  
  for (const pattern of suspiciousPatterns) {
    if (fileContent.includes(pattern)) {
      errors.push('File content contains suspicious patterns');
      break;
    }
  }
  
  return errors;
}

/**
 * Generate secure filename with timestamp and hash
 */
function generateSecureFileName(originalName, userId) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const hash = crypto.createHash('sha256')
    .update(userId + originalName + Date.now())
    .digest('hex')
    .substring(0, 8);
  
  const extension = originalName.split('.').pop();
  return `${timestamp}_${hash}_${originalName}`;
}

/* ------------------------------------------------------------------ */
/* 4. Main Cloud Function Handler                                     */
/* ------------------------------------------------------------------ */
exports.saver = async (req, res) => {
  const startTime = Date.now();
  // Add debugging
  console.log('Request headers:', req.headers);
  console.log('Request method:', req.method);
  console.log('Content-Type:', req.headers['content-type']);
  
  // Get client IP for rate limiting
  const clientIP = req.headers['x-forwarded-for'] || 
                   req.connection.remoteAddress || 
                   'unknown';
  
  console.log(`[${new Date().toISOString()}] ${req.method} request from ${clientIP}`);
  
  /* ---- 4.1 CORS pre-flight handling ------------------------------ */
  if (req.method === 'OPTIONS') {
    res.status(200).set(corsHeaders).end();
    return;
  }
  
  // Set CORS headers for all responses
  Object.keys(corsHeaders).forEach(key => {
    res.set(key, corsHeaders[key]);
  });
  
  /* ---- 4.2 Method validation ------------------------------------- */
  if (req.method !== 'POST') {
    res.status(405).json({ 
      error: 'Method not allowed', 
      allowed: ['POST', 'OPTIONS'] 
    });
    return;
  }
  
  /* ---- 4.3 Rate limiting ----------------------------------------- */
  if (!checkRateLimit(clientIP)) {
    console.warn(`Rate limit exceeded for IP: ${clientIP}`);
    res.status(429).json({ 
      error: 'Rate limit exceeded',
      retryAfter: RATE_LIMIT_WINDOW / 1000
    });
    return;
  }
  
  /* ---- 4.4 File processing with Busboy --------------------------- */
  const busboyInstance = busboy({ 
    headers: req.headers,
    limits: {
      fileSize: MAX_FILE_SIZE
    }
  });
  
  let fileBuffer = Buffer.alloc(0);
  let fileName = '';
  let mimeType = '';
  let uploadCompleted = false;
  
  // Handle file upload
  busboyInstance.on('file', (fieldname, file, fileInfo) => {
    fileName = fileInfo.filename;
    mimeType = fileInfo.mimeType;
    
    const chunks = [];
    
    file.on('data', (data) => {
      chunks.push(data);
    });
    
    file.on('end', () => {
      fileBuffer = Buffer.concat(chunks);
    });
    
    file.on('error', (error) => {
      console.error('File stream error:', error);
      if (!uploadCompleted) {
        uploadCompleted = true;
        res.status(500).json({ 
          error: 'File upload failed',
          processingTime: Date.now() - startTime
        });
      }
    });
  });
  
  // Handle upload completion
  busboyInstance.on('finish', async () => {
    if (uploadCompleted) return;
    
    try {
      // Validate file
      const validationErrors = validateFile(fileName, fileBuffer, mimeType);
      if (validationErrors.length > 0) {
        throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
      }
      
      // Extract user ID from filename for additional validation
      const userIdMatch = fileName.match(/^([a-f0-9]{32})_/);
      if (!userIdMatch) {
        throw new Error('Invalid filename format - missing user ID');
      }
      
      const userId = userIdMatch[1];
      
      // Generate secure filename
      const secureFileName = generateSecureFileName(fileName, userId);
      const filePath = `${UPLOAD_PREFIX}${secureFileName}`;
      
      /* ---- 4.5 Upload to Google Cloud Storage -------------------- */
      const bucket = storage.bucket(BUCKET_NAME);
      const file = bucket.file(filePath);
      
      const stream = file.createWriteStream({
        metadata: {
          contentType: mimeType,
          metadata: {
            originalName: fileName,
            uploadTime: new Date().toISOString(),
            clientIP: clientIP,
            userId: userId
          }
        },
        resumable: false
      });
      
      stream.on('error', (error) => {
        console.error('GCS upload error:', error);
        console.error('Error details:', error.message, error.stack);
        if (!uploadCompleted) {
          uploadCompleted = true;
          res.status(500).json({ 
            error: 'Upload to storage failed',
            details: error.message,
            processingTime: Date.now() - startTime
          });
        }
      });
      
      stream.on('finish', () => {
        if (!uploadCompleted) {
          uploadCompleted = true;
          
          const processingTime = Date.now() - startTime;
          const publicUrl = `https://storage.googleapis.com/${BUCKET_NAME}/${filePath}`;
          
          console.log(`[${new Date().toISOString()}] Upload successful: ${secureFileName} (${processingTime}ms)`);
          
          res.status(200).json({
            success: true,
            url: publicUrl,
            fileName: secureFileName,
            originalName: fileName,
            size: fileBuffer.length,
            processingTime
          });
        }
      });
      
      stream.end(fileBuffer);
      
    } catch (error) {
      if (!uploadCompleted) {
        uploadCompleted = true;
        
        const processingTime = Date.now() - startTime;
        
        console.error(`[${new Date().toISOString()}] Upload error (${processingTime}ms):`, {
          error: error.message,
          stack: error.stack,
          clientIP
        });
        
        // Don't expose internal error details to client
        const userMessage = error.message.includes('Validation failed') || 
                           error.message.includes('Rate limit') ||
                           error.message.includes('Invalid filename')
          ? error.message
          : 'Upload failed due to server error';
        
        res.status(error.message.includes('Rate limit') ? 429 : 
                   error.message.includes('Validation failed') ? 400 : 500)
           .json({
              success: false,
              error: userMessage,
              processingTime
           });
      }
    }
  });
  
  // Handle parsing errors
  busboyInstance.on('error', (error) => {
    console.error('Busboy error:', error);
    if (!uploadCompleted) {
      uploadCompleted = true;
      res.status(400).json({ 
        error: 'Invalid request format',
        processingTime: Date.now() - startTime
      });
    }
  });
  
  // Pipe request to busboy
  req.pipe(busboyInstance);
};
