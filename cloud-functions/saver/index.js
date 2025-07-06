// cloud-functions/saver/index.js

const { Storage } = require('@google-cloud/storage');
const busboy = require('busboy');
const crypto = require('crypto');
const path = require('path');

// Initialize Cloud Storage
const storage = new Storage();
const BUCKET_NAME = 'fake-profile-detection-eda-bucket';
const UPLOAD_PREFIX = 'uploads/';

// Configuration
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_MIME_TYPES = [
  'application/json',
  'text/csv',
  'text/plain'
];

// CORS headers
// const corsHeaders = {
//   'Access-Control-Allow-Origin': '*', // TODO: Change to 'https://fakeprofiledetection.github.io'
//   'Access-Control-Allow-Methods': 'POST, OPTIONS',
//   'Access-Control-Allow-Headers': 'Content-Type',
//   'Access-Control-Max-Age': '3600'
// };

const corsHeaders = {
  'Access-Control-Allow-Origin': '*', // TODO: Change back to 'https://fakeprofiledetection.github.io'
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '3600',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
};

// Rate limiting store
const rateLimitStore = new Map();
const RATE_LIMIT_WINDOW = 60 * 1000;
const RATE_LIMIT_MAX_REQUESTS = 30;

function checkRateLimit(clientIP) {
  const now = Date.now();
  const windowStart = now - RATE_LIMIT_WINDOW;
  
  const requests = rateLimitStore.get(clientIP) || [];
  const recentRequests = requests.filter(time => time > windowStart);
  
  if (recentRequests.length >= RATE_LIMIT_MAX_REQUESTS) {
    return false;
  }
  
  recentRequests.push(now);
  rateLimitStore.set(clientIP, recentRequests);
  return true;
}

/**
 * Extract user ID from various filename formats:
 * - platform_userid_taskid.csv (platform keystroke data)
 * - platform_userid_taskid_raw.txt (platform raw text data)
 * - platform_userid_taskid_metadata.json (platform metadata)
 * - userid_consent.json
 * - userid_demographics.json
 * - userid_start_study.json
 * - userid_completion.json
 */
function extractUserIdFromFilename(filename) {
  console.log('Extracting user ID from filename:', filename);
  
  // Pattern 1: Platform files - <platform>_<userid>_<taskid>_<.csv | _raw.txt | .metadata.json>
  // Example: f_1234567890abcdef1234567890abcdef_1.csv
  // Example: i_1234567890abcdef1234567890abcdef_1_raw.txt
  // Example: t_1234567890abcdef1234567890abcdef_1_metadata.json
  // Where platform is f (Facebook), i (Instagram), or t (Twitter)
  const platformPattern = /^[fit]_([a-f0-9]{32})_[0-9]+_(.*\.(csv|raw\.txt|metadata\.json))$/;

  const platformMatch = filename.match(platformPattern);
  if (platformMatch) {
    console.log('Matched platform pattern, user ID:', platformMatch[1]);
    return platformMatch[1];
  }
  
  // Pattern 2: Direct user ID files - <userid>_<type>.json
  // Example: 1234567890abcdef1234567890abcdef_consent.json
  // Example: 1234567890abcdef1234567890abcdef_demographics.json
  const directPattern = /^([a-f0-9]{32})_(consent|demographics|start_study|completion)\.json$/;
  const directMatch = filename.match(directPattern);
  if (directMatch) {
    console.log('Matched direct pattern, user ID:', directMatch[1]);
    return directMatch[1];
  }
  
  console.log('No user ID pattern matched');
  return null;
}

exports.saver = async (req, res) => {
  const startTime = Date.now();
  
  // Set CORS headers
  Object.keys(corsHeaders).forEach(key => {
    res.set(key, corsHeaders[key]);
  });
  
  // Handle OPTIONS
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  // Only accept POST
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  
  // Get client IP
  const clientIP = req.headers['x-forwarded-for'] || 'unknown';
  
  console.log(`[${new Date().toISOString()}] ${req.method} request from ${clientIP}`);
  
  // Rate limiting
  if (!checkRateLimit(clientIP)) {
    console.warn(`Rate limit exceeded for IP: ${clientIP}`);
    res.status(429).json({ 
      error: 'Rate limit exceeded',
      retryAfter: RATE_LIMIT_WINDOW / 1000
    });
    return;
  }
  
  try {
    // Use req.rawBody if available (Cloud Functions provides this)
    const buffer = req.rawBody || req.body;
    
    if (!buffer) {
      throw new Error('No request body received');
    }
    
    console.log(`Raw body length: ${buffer.length} bytes`);
    
    // Parse multipart form data
    const result = await parseMultipartData(buffer, req.headers);
    
    if (!result.file) {
      throw new Error('No file found in request');
    }
    
    console.log('File parsed:', {
      fileName: result.file.filename,
      size: result.file.data.length,
      mimeType: result.file.mimeType
    });
    
    // Validate file
    const validationErrors = validateFile(
      result.file.filename,
      result.file.data,
      result.file.mimeType
    );
    
    if (validationErrors.length > 0) {
      throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
    }
    
    // Extract user ID from filename
    const userId = extractUserIdFromFilename(result.file.filename);
    if (!userId) {
      console.error('Could not extract user ID from filename:', result.file.filename);
      throw new Error('Invalid filename format - could not extract user ID');
    }
    
    // Generate GCS filename - keep original structure but add timestamp prefix
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const hash = crypto.createHash('sha256')
      .update(userId + result.file.filename + Date.now())
      .digest('hex')
      .substring(0, 8);
    
    // Preserve original filename in GCS path
    const gcsFileName = `${UPLOAD_PREFIX}${timestamp}_${hash}_${result.file.filename}`;
    
    console.log('Uploading to GCS:', gcsFileName);
    
    // Upload to GCS
    const bucket = storage.bucket(BUCKET_NAME);
    const file = bucket.file(gcsFileName);
    
    await file.save(result.file.data, {
      metadata: {
        contentType: result.file.mimeType,
        metadata: {
          originalName: result.file.filename,
          uploadTime: new Date().toISOString(),
          clientIP: clientIP,
          userId: userId
        }
      }
    });
    
    console.log('Upload successful');
    
    const publicUrl = `https://storage.googleapis.com/${BUCKET_NAME}/${gcsFileName}`;
    const processingTime = Date.now() - startTime;
    
    // Return response matching Netlify format
    res.status(200).json({
      success: true,
      url: publicUrl,
      fileName: gcsFileName,
      originalName: result.file.filename,
      size: result.file.data.length,
      processingTime
    });
    
  } catch (error) {
    console.error('Upload error:', error);
    
    const processingTime = Date.now() - startTime;
    let statusCode = 500;
    let userMessage = 'Upload failed due to server error';
    
    if (error.message.includes('Rate limit')) {
      statusCode = 429;
      userMessage = error.message;
    } else if (
      error.message.includes('Validation failed') ||
      error.message.includes('No file found') ||
      error.message.includes('Invalid filename') ||
      error.message.includes('could not extract user ID')
    ) {
      statusCode = 400;
      userMessage = error.message;
    }
    
    res.status(statusCode).json({
      success: false,
      error: userMessage,
      processingTime
    });
  }
};

// Parse multipart form data
async function parseMultipartData(buffer, headers) {
  return new Promise((resolve, reject) => {
    const result = { fields: {}, file: null };
    
    try {
      const bb = busboy({ 
        headers: headers,
        limits: {
          fileSize: MAX_FILE_SIZE
        }
      });
      
      let fileData = null;
      
      bb.on('file', (name, file, info) => {
        console.log(`File [${name}]: filename: ${info.filename}, encoding: ${info.encoding}, mimeType: ${info.mimeType}`);
        
        const chunks = [];
        
        file.on('data', (data) => {
          chunks.push(data);
        });
        
        file.on('end', () => {
          fileData = {
            fieldname: name,
            filename: info.filename,
            encoding: info.encoding,
            mimeType: info.mimeType || 'application/octet-stream',
            data: Buffer.concat(chunks)
          };
        });
        
        file.on('error', (err) => {
          reject(err);
        });
      });
      
      bb.on('field', (name, val) => {
        result.fields[name] = val;
      });
      
      bb.on('finish', () => {
        result.file = fileData;
        resolve(result);
      });
      
      bb.on('error', (err) => {
        reject(err);
      });
      
      // Write the buffer to busboy
      bb.end(buffer);
      
    } catch (err) {
      reject(err);
    }
  });
}

// Validate file
function validateFile(fileName, fileBuffer, contentType) {
  const errors = [];
  
  if (!fileName || fileName.length > 255) {
    errors.push('Invalid file name');
  }
  
  if (fileBuffer.length > MAX_FILE_SIZE) {
    errors.push(`File size exceeds limit of ${MAX_FILE_SIZE / 1024 / 1024}MB`);
  }
  
  // Updated sanitization check - allow underscores and numbers in filename
  const sanitizedName = fileName.replace(/[^a-zA-Z0-9._-]/g, '');
  if (sanitizedName !== fileName) {
    errors.push('File name contains invalid characters');
  }
  
  // Determine content type from extension if needed
  if (!contentType || contentType === 'application/octet-stream') {
    const ext = path.extname(fileName).toLowerCase();
    switch (ext) {
      case '.json':
        contentType = 'application/json';
        break;
      case '.csv':
        contentType = 'text/csv';
        break;
      case '.txt':
        contentType = 'text/plain';
        break;
    }
  }
  
  if (!ALLOWED_MIME_TYPES.includes(contentType)) {
    errors.push(`File type not allowed. Allowed types: ${ALLOWED_MIME_TYPES.join(', ')}`);
  }
  
  // Validate JSON content
  if (contentType === 'application/json') {
    try {
      JSON.parse(fileBuffer.toString());
    } catch (e) {
      errors.push('Invalid JSON content');
    }
  }
  
  // Check for suspicious patterns
  const content = fileBuffer.toString().toLowerCase();
  const suspiciousPatterns = ['<script', 'javascript:', 'eval(', 'document.cookie'];
  
  for (const pattern of suspiciousPatterns) {
    if (content.includes(pattern)) {
      errors.push('File content contains suspicious patterns');
      break;
    }
  }
  
  return errors;
}
