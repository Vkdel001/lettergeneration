# SMS Link Feature - Complete Specification

## **📋 Overview**

This document outlines the SMS Link feature - an **additional functionality** that generates unique web links for each customer's arrears letter, creates shortened URLs, and produces an SMS bulk file for third-party SMS sending.

**Important:** This is an **ADD-ON feature** that works alongside existing PDF generation. All current functionality remains unchanged.

---

## **🎯 Feature Purpose**

### **Business Goal:**
- Provide customers with instant access to their arrears letters via SMS
- Reduce dependency on email delivery
- Enable mobile-friendly letter viewing
- Generate bulk SMS files for third-party SMS services

### **User Experience:**
1. Customer receives SMS with short link
2. Clicks link → Opens letter in mobile browser
3. Views letter content online
4. Downloads PDF if needed

---

## **🔧 Technical Architecture**

### **Component 1: Frontend UI Enhancement**

#### **New UI Elements in Main Interface:**

**Location:** After existing "Generate PDFs" and "Combine PDFs" buttons

```
┌─────────────────────────────────────────┐
│ [Generate PDFs] [Combine PDFs]          │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │     📱 SMS Link Generation          │ │
│ │                                     │ │
│ │ [Generate SMS Links] [Download SMS] │ │
│ │                                     │ │
│ │ Status: Ready / Processing / Done   │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### **Button Functionality:**

**1. "Generate SMS Links" Button:**
- **Trigger:** User clicks after PDFs are generated
- **Action:** Creates unique URLs for each customer
- **Status:** Shows progress (Processing... / Complete)
- **Requirement:** PDFs must exist first

**2. "Download SMS File" Button:**
- **Trigger:** Available after SMS links generated
- **Action:** Downloads CSV file with SMS data
- **File:** `SMS_Batch_[Template]_[Date].csv`

---

### **Component 2: Backend API Endpoints**

#### **New API Routes:**

```javascript
// Generate SMS links for existing PDFs
POST /api/generate-sms-links
Body: { 
  outputFolder: "output_sph_November2025",
  template: "SPH_Fresh.py" 
}
Response: { 
  success: true, 
  linksGenerated: 1500,
  smsFileReady: true 
}

// Download SMS bulk file
GET /api/download-sms-file/:outputFolder
Response: CSV file download

// View individual letter (customer-facing)
GET /letter/:uniqueId
Response: HTML letter page

// Get letter data for viewer
GET /api/letter-data/:uniqueId
Response: { letterData, pdfDownloadUrl }
```

---

### **Component 3: Letter Data Storage**

#### **Storage Structure:**

**File-based approach (JSON files):**
```
letter_links/
├── output_sph_November2025/
│   ├── abc123def456.json     # Letter 1 data
│   ├── xyz789ghi012.json     # Letter 2 data
│   └── sms_batch.csv         # SMS bulk file
└── output_jph_November2025/
    ├── def456abc123.json
    └── sms_batch.csv
```

**Individual Letter Data (JSON):**
```json
{
  "id": "abc123def456",
  "policyNo": "00407/0094507",
  "customerName": "Mr John Doe",
  "mobileNo": "57123456",
  "pdfPath": "/output_sph_November2025/protected/001_00407_0094507_Mr_John_Doe.pdf",
  "letterContent": {
    "date": "30-November-2025",
    "address": ["Mr John Doe", "123 Main Street", "Port Louis"],
    "salutation": "Dear Mr Doe,",
    "policyDetails": {
      "policyNo": "00407/0094507",
      "premium": "MUR 1,387.40",
      "frequency": "Monthly",
      "arrearsAmount": "MUR 2,774.80"
    },
    "bodyText": "You are hereby notified that the premiums due...",
    "qrCodeData": "payment_qr_string"
  },
  "createdAt": "2025-11-07T10:30:00Z",
  "expiresAt": "2025-12-07T10:30:00Z",
  "accessCount": 0,
  "maxAccess": 10,
  "isActive": true
}
```

---

### **Component 4: SMS Bulk File Generation**

#### **CSV File Structure:**
```csv
Mobile,Message,ShortURL,Policy,CustomerName,Status
57123456,"Dear Mr Doe, your NICL arrears notice: https://tinyurl.com/abc123",https://tinyurl.com/abc123,00407/0094507,Mr John Doe,Ready
57789012,"Dear Mrs Smith, your NICL arrears notice: https://tinyurl.com/def456",https://tinyurl.com/def456,00407/0094508,Mrs Jane Smith,Ready
```

#### **SMS Message Template:**
```
Dear [Title] [Surname], your NICL arrears notice is ready. 
View online: [ShortURL]
Valid for 30 days.
```

---

### **Component 5: Customer Letter Viewer**

#### **New Frontend Route:**
```
URL: https://your-domain.com/letter/abc123def456
Component: LetterViewer.jsx
```

#### **Letter Viewer Features:**

**Mobile-Responsive Design:**
```html
<div class="letter-viewer">
  <header class="letter-header">
    <img src="/logo.png" alt="NICL Logo" />
    <h1>National Insurance Co. Ltd</h1>
  </header>
  
  <div class="letter-content">
    <div class="date">30-November-2025</div>
    
    <div class="address">
      <p>Mr John Doe</p>
      <p>123 Main Street</p>
      <p>Port Louis</p>
    </div>
    
    <h2>NOTICE: MISE EN DEMEURE</h2>
    <p class="article">Article 1983-21, 3382-4(Code Civil)</p>
    
    <p class="salutation">Dear Mr Doe,</p>
    
    <table class="policy-details">
      <tr><td>POLICY NO.</td><td>00407/0094507</td></tr>
      <tr><td>PREMIUM</td><td>MUR 1,387.40</td></tr>
      <tr><td>PAYMENT FREQUENCY</td><td>Monthly</td></tr>
    </table>
    
    <div class="body-text">
      <p>You are hereby notified that the premiums due by you...</p>
      <!-- Full letter content -->
    </div>
    
    <div class="qr-section">
      <p>For your convenience, you may settle payments via QR code:</p>
      <img src="/api/qr/abc123def456" alt="Payment QR Code" />
    </div>
  </div>
  
  <div class="actions">
    <button class="download-btn" onclick="downloadPDF()">
      📄 Download PDF
    </button>
    <button class="print-btn" onclick="window.print()">
      🖨️ Print Letter
    </button>
  </div>
  
  <footer class="letter-footer">
    <p>This letter expires on: 07-December-2025</p>
    <p>For assistance: nicarlife@nicl.mu | 602-3315</p>
  </footer>
</div>
```

---

## **🔄 Complete Workflow**

### **Step 1: User Generates PDFs (Existing)**
```
1. User uploads Excel file
2. Selects template (SPH/JPH/Company/MED)
3. Clicks "Generate PDFs"
4. PDFs created in output folder
```

### **Step 2: User Generates SMS Links (NEW)**
```
1. User clicks "Generate SMS Links" button
2. System processes each PDF:
   - Extracts customer data
   - Creates unique ID
   - Generates long URL
   - Creates short URL via TinyURL API
   - Saves letter data as JSON
3. Creates SMS bulk CSV file
4. Shows "SMS Links Generated" status
```

### **Step 3: User Downloads SMS File (NEW)**
```
1. User clicks "Download SMS File" button
2. Downloads CSV with mobile numbers and SMS text
3. User imports CSV into third-party SMS tool
4. Sends bulk SMS to customers
```

### **Step 4: Customer Experience (NEW)**
```
1. Customer receives SMS with short link
2. Clicks link → Opens letter viewer page
3. Views letter content on mobile/desktop
4. Can download PDF or print letter
5. Link expires after 30 days
```

---

## **🛠️ Implementation Details**

### **Phase 1: Core Infrastructure**

#### **Backend Changes:**

**1. New Python Function (add to all templates):**
```python
def generate_sms_links(output_folder, df):
    """Generate unique URLs and SMS file for all customers"""
    
    letter_links = []
    sms_data = []
    
    for index, row in df.iterrows():
        # Extract customer data
        mobile = row.get('MOBILE_NO', '')
        name = build_customer_name(row)
        policy = row.get('Policy No', '')
        
        # Generate unique ID
        unique_id = generate_unique_id(policy, index)
        
        # Create letter data
        letter_data = extract_letter_data(row, index)
        
        # Save letter data
        save_letter_json(unique_id, letter_data, output_folder)
        
        # Generate URLs
        long_url = f"https://your-domain.com/letter/{unique_id}"
        short_url = create_short_url(long_url)
        
        # Prepare SMS data
        sms_text = f"Dear {name}, your NICL arrears notice: {short_url}"
        sms_data.append({
            'Mobile': mobile,
            'Message': sms_text,
            'ShortURL': short_url,
            'Policy': policy,
            'CustomerName': name,
            'Status': 'Ready'
        })
    
    # Save SMS bulk file
    save_sms_csv(sms_data, output_folder)
    
    return len(sms_data)
```

**2. New Server.js Endpoints:**
```javascript
// Generate SMS links
app.post('/api/generate-sms-links', (req, res) => {
  const { outputFolder, template } = req.body;
  
  // Call Python function to generate links
  const pythonArgs = [
    'generate_sms_links.py',
    '--folder', outputFolder,
    '--template', template
  ];
  
  const python = spawn('python', pythonArgs);
  // Handle response...
});

// Download SMS file
app.get('/api/download-sms-file/:folder', (req, res) => {
  const smsFile = `${req.params.folder}/sms_batch.csv`;
  res.download(smsFile);
});

// Letter viewer API
app.get('/api/letter-data/:id', (req, res) => {
  const letterData = loadLetterData(req.params.id);
  
  // Check expiration and access limits
  if (isExpired(letterData) || exceedsAccessLimit(letterData)) {
    return res.status(410).json({ error: 'Letter no longer available' });
  }
  
  // Increment access count
  incrementAccessCount(req.params.id);
  
  res.json(letterData);
});
```

#### **Frontend Changes:**

**1. New UI Components:**
```jsx
// Add to main interface
function SMSLinkSection({ outputFolder, onSMSGenerated }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [smsReady, setSmsReady] = useState(false);
  
  const generateSMSLinks = async () => {
    setIsGenerating(true);
    
    const response = await fetch('/api/generate-sms-links', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ outputFolder, template: selectedTemplate })
    });
    
    const result = await response.json();
    setSmsReady(result.success);
    setIsGenerating(false);
    onSMSGenerated(result);
  };
  
  const downloadSMSFile = () => {
    window.open(`/api/download-sms-file/${outputFolder}`);
  };
  
  return (
    <div className="sms-section">
      <h3>📱 SMS Link Generation</h3>
      
      <button 
        onClick={generateSMSLinks} 
        disabled={isGenerating}
        className="generate-sms-btn"
      >
        {isGenerating ? 'Generating Links...' : 'Generate SMS Links'}
      </button>
      
      {smsReady && (
        <button 
          onClick={downloadSMSFile}
          className="download-sms-btn"
        >
          📥 Download SMS File
        </button>
      )}
      
      <div className="sms-status">
        Status: {isGenerating ? 'Processing...' : smsReady ? 'Ready' : 'Not Generated'}
      </div>
    </div>
  );
}
```

**2. Letter Viewer Component:**
```jsx
// New route: /letter/:id
function LetterViewer() {
  const { id } = useParams();
  const [letter, setLetter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch(`/api/letter-data/${id}`)
      .then(res => {
        if (!res.ok) throw new Error('Letter not found or expired');
        return res.json();
      })
      .then(data => {
        setLetter(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);
  
  const downloadPDF = () => {
    window.open(`/api/download-pdf/${id}`);
  };
  
  if (loading) return <div className="loading">Loading letter...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  
  return (
    <div className="letter-viewer">
      {/* Render letter content */}
      <LetterContent data={letter.letterContent} />
      
      <div className="actions">
        <button onClick={downloadPDF} className="download-btn">
          📄 Download PDF
        </button>
      </div>
    </div>
  );
}
```

---

### **Phase 2: URL Shortening Integration**

#### **TinyURL Integration:**
```javascript
async function createShortURL(longURL) {
  try {
    const response = await fetch(`https://tinyurl.com/api-create.php?url=${encodeURIComponent(longURL)}`);
    const shortURL = await response.text();
    return shortURL.trim();
  } catch (error) {
    console.error('URL shortening failed:', error);
    return longURL; // Fallback to long URL
  }
}
```

#### **Alternative: Bitly Integration (Premium):**
```javascript
async function createShortURLBitly(longURL) {
  const response = await fetch('https://api-ssl.bitly.com/v4/shorten', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${BITLY_ACCESS_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ long_url: longURL })
  });
  
  const data = await response.json();
  return data.link;
}
```

---

### **Phase 3: Security & Performance**

#### **Security Measures:**
```javascript
// Unique ID generation
function generateUniqueId(policyNo, index) {
  const crypto = require('crypto');
  const data = `${policyNo}-${index}-${Date.now()}-${Math.random()}`;
  return crypto.createHash('sha256').update(data).digest('hex').substring(0, 16);
}

// Access control
function checkAccess(letterData) {
  const now = new Date();
  const expires = new Date(letterData.expiresAt);
  
  if (now > expires) {
    return { valid: false, reason: 'expired' };
  }
  
  if (letterData.accessCount >= letterData.maxAccess) {
    return { valid: false, reason: 'access_limit' };
  }
  
  return { valid: true };
}
```

#### **Performance Optimizations:**
- **Lazy loading** - Generate links only when requested
- **Caching** - Cache letter data in memory
- **Compression** - Gzip letter content
- **CDN** - Serve static assets via CDN

---

## **📊 File Structure Changes**

### **New Files to Create:**

```
project/
├── src/
│   ├── components/
│   │   ├── SMSLinkSection.jsx      # NEW: SMS generation UI
│   │   ├── LetterViewer.jsx        # NEW: Customer letter viewer
│   │   └── LetterContent.jsx       # NEW: Letter content renderer
│   └── styles/
│       └── letter-viewer.css       # NEW: Letter viewer styles
├── backend/
│   ├── generate_sms_links.py       # NEW: SMS link generation script
│   ├── letter_data_manager.py      # NEW: Letter data operations
│   └── url_shortener.js            # NEW: URL shortening utilities
└── letter_links/                   # NEW: Letter data storage
    ├── output_sph_November2025/
    ├── output_jph_November2025/
    └── ...
```

### **Modified Files:**

```
src/App.jsx                         # Add new route for letter viewer
server.js                           # Add new API endpoints
SPH_Fresh.py                        # Add SMS generation function
JPH_Fresh.py                        # Add SMS generation function
Company_Fresh.py                    # Add SMS generation function
MED_SPH_Fresh_Signature.py          # Add SMS generation function
MED_JPH_Fresh_Signature.py          # Add SMS generation function
```

---

## **🎯 User Interface Flow**

### **Main Interface Enhancement:**

```
┌─────────────────────────────────────────────────────────────┐
│                    NICL PDF Generator                       │
├─────────────────────────────────────────────────────────────┤
│ 📁 File Upload: [Choose File] output_sph_november.xlsx     │
│ 📋 Template: SPH Template (Auto-selected)                  │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                PDF Generation                           │ │
│ │ [Generate PDFs] [Combine PDFs]                         │ │
│ │ Status: ✅ 1,500 PDFs Generated                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                📱 SMS Link Generation                   │ │
│ │                                                         │ │
│ │ Generate unique web links for each customer letter      │ │
│ │                                                         │ │
│ │ [Generate SMS Links] [📥 Download SMS File]            │ │
│ │                                                         │ │
│ │ Status: ⏳ Processing... / ✅ 1,500 Links Generated    │ │
│ │                                                         │ │
│ │ 📋 SMS File: SMS_Batch_SPH_Nov2025.csv (Ready)        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **Customer Letter Viewer:**

```
┌─────────────────────────────────────────────────────────────┐
│                🏢 NICL - Letter Viewer                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📅 30-November-2025                                       │
│                                                             │
│  Mr John Doe                                               │
│  123 Main Street                                           │
│  Port Louis                                                │
│                                                             │
│  ⚖️ NOTICE: MISE EN DEMEURE                               │
│  Article 1983-21, 3382-4(Code Civil)                      │
│                                                             │
│  Dear Mr Doe,                                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ POLICY NO.     │ 00407/0094507                      │   │
│  │ PREMIUM        │ MUR 1,387.40                       │   │
│  │ FREQUENCY      │ Monthly                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  You are hereby notified that the premiums due...          │
│                                                             │
│  [QR Code Image]                                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [📄 Download PDF] [🖨️ Print Letter]                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  📱 This letter expires: 07-December-2025                 │
│  📧 Contact: nicarlife@nicl.mu | ☎️ 602-3315              │
└─────────────────────────────────────────────────────────────┘
```

---

## **📈 Expected Benefits**

### **Operational Benefits:**
- **Instant Delivery:** SMS reaches customers immediately
- **Higher Open Rates:** SMS has 98% open rate vs 20% email
- **Cost Reduction:** No printing, postage, or email delivery costs
- **Better Tracking:** Know who viewed their letter
- **Mobile Friendly:** Optimized for smartphone viewing

### **Customer Benefits:**
- **Convenience:** View letter anywhere, anytime
- **Accessibility:** Works on any device with internet
- **Immediate Access:** No waiting for mail delivery
- **Download Option:** Save PDF for records
- **Print Option:** Print at home if needed

### **Technical Benefits:**
- **Scalable:** Handle thousands of customers
- **Secure:** Unique URLs with expiration
- **Flexible:** Easy to update letter templates
- **Integrated:** Works with existing PDF system
- **Analytics:** Track customer engagement

---

## **💰 Cost Considerations**

### **SMS Costs:**
- **Bulk SMS:** ~MUR 0.50 - 1.00 per SMS
- **1,500 customers:** ~MUR 750 - 1,500 per batch
- **Monthly savings:** Eliminate printing/postage costs

### **Infrastructure Costs:**
- **Storage:** Minimal (JSON files)
- **Bandwidth:** Low (HTML pages)
- **URL Shortening:** Free (TinyURL) or ~$29/month (Bitly Pro)

### **Development Costs:**
- **One-time development:** ~1 week effort
- **Maintenance:** Minimal ongoing costs

---

## **🚀 Implementation Timeline**

### **Week 1: Core Development**
- **Day 1-2:** Backend API endpoints
- **Day 3-4:** SMS link generation in Python
- **Day 5:** Frontend UI components

### **Week 2: Integration & Testing**
- **Day 1-2:** Letter viewer component
- **Day 3:** URL shortening integration
- **Day 4-5:** Testing and bug fixes

### **Week 3: Deployment & Refinement**
- **Day 1-2:** VPS deployment
- **Day 3-4:** User testing and feedback
- **Day 5:** Final adjustments and documentation

---

## **✅ Success Criteria**

### **Functional Requirements:**
- ✅ Generate unique URLs for each customer
- ✅ Create mobile-responsive letter viewer
- ✅ Produce SMS bulk file with correct format
- ✅ Integrate URL shortening service
- ✅ Implement security (expiration, access limits)

### **Performance Requirements:**
- ✅ Generate 1,500+ links within 2 minutes
- ✅ Letter viewer loads within 3 seconds
- ✅ Handle 100+ concurrent letter views
- ✅ 99.9% uptime for letter viewer

### **User Experience Requirements:**
- ✅ Intuitive UI for SMS generation
- ✅ Clear status indicators
- ✅ Easy SMS file download
- ✅ Mobile-friendly letter viewer
- ✅ Graceful error handling

---

## **🔒 Security & Privacy**

### **Data Protection:**
- **Unique IDs:** Non-guessable identifiers
- **Expiration:** 30-day automatic expiry
- **Access Limits:** Maximum 10 views per link
- **HTTPS Only:** Secure transmission
- **No Indexing:** Prevent search engine crawling

### **Privacy Compliance:**
- **Data Retention:** Delete expired letters
- **Access Logging:** Track who viewed what
- **Consent:** Customer consent via SMS acceptance
- **Anonymization:** No personal data in URLs

---

This comprehensive specification covers all aspects of the SMS Link feature as an additional functionality to the existing PDF generation system. The feature provides a modern, mobile-friendly way for customers to access their arrears letters while maintaining all current capabilities.