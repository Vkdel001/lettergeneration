# URL Mappings Cleanup & Expiration System

## Date: February 12, 2026

## Problem Statement

The `url_mappings.json` file grows indefinitely as new SMS links are generated. Without cleanup:
- File size increases continuously (could reach MBs/GBs)
- Performance degrades (slower read/write operations)
- Memory usage increases (entire file loaded into memory)
- Disk space wasted on old/unused links

## Solution Overview

Implement automatic expiration and cleanup system with archiving:
- Add expiration timestamp to each URL mapping
- Automatically remove expired entries
- Archive old entries for historical reference
- Keep active mappings file small and performant

## Specifications

### Expiration Policy
- **Link Validity**: 90 days from creation
- **Cleanup Frequency**: Daily at 2:00 AM
- **Archive Retention**: Indefinite (archived files kept for audit)

### Data Structure Changes

**Current Structure:**
```json
{
  "abc123": {
    "longUrl": "http://localhost:3001/letter/unique123",
    "clicks": 5,
    "createdAt": 1707696000000,
    "lastAccessed": 1707782400000
  }
}
```

**New Structure (with expiration):**
```json
{
  "abc123": {
    "longUrl": "http://localhost:3001/letter/unique123",
    "clicks": 5,
    "createdAt": 1707696000000,
    "expiresAt": 1715472000000,
    "lastAccessed": 1707782400000
  }
}
```

### Cleanup Logic

1. **Check Expiration**: Compare current time with `expiresAt`
2. **Separate Active/Expired**: Split mappings into two groups
3. **Archive Expired**: Save expired entries to dated archive file
4. **Update Active**: Save only active entries to main file
5. **Log Results**: Report cleanup statistics

### Archive File Naming

Format: `url_mappings_archive_YYYY-MM-DD.json`

Examples:
- `url_mappings_archive_2026-02-12.json`
- `url_mappings_archive_2026-03-15.json`

## Implementation Details

### Files Modified

1. **server.js**
   - Add `cleanupExpiredMappings()` function
   - Add daily scheduler (runs at 2:00 AM)
   - Add expiration check in redirect handler
   - Add logging for cleanup operations

2. **generate_sms_links.py**
   - Add `expiresAt` field when creating new mappings
   - Calculate expiration: `createdAt + 90 days`
   - Maintain backward compatibility with existing mappings

### Code Changes

#### server.js - Cleanup Function

```javascript
// Cleanup expired URL mappings and archive them
function cleanupExpiredMappings() {
  try {
    const now = Date.now();
    const mappings = loadUrlMappings();
    const expirationTime = 90 * 24 * 60 * 60 * 1000; // 90 days in milliseconds
    
    const active = {};
    const expired = {};
    
    // Separate active and expired mappings
    for (const [shortId, data] of Object.entries(mappings)) {
      if (data.expiresAt && now > data.expiresAt) {
        expired[shortId] = data;
      } else if (!data.expiresAt && (now - data.createdAt) > expirationTime) {
        // Handle old mappings without expiresAt field
        expired[shortId] = data;
      } else {
        active[shortId] = data;
      }
    }
    
    // Save active mappings
    saveUrlMappings(active);
    
    // Archive expired mappings if any
    if (Object.keys(expired).length > 0) {
      const archiveFile = `url_mappings_archive_${new Date().toISOString().split('T')[0]}.json`;
      fs.writeFileSync(archiveFile, JSON.stringify(expired, null, 2));
      console.log(`[CLEANUP] Archived ${Object.keys(expired).length} expired mappings to ${archiveFile}`);
    }
    
    console.log(`[CLEANUP] Active: ${Object.keys(active).length}, Expired: ${Object.keys(expired).length}`);
    
  } catch (error) {
    console.error('[CLEANUP] Error during cleanup:', error);
  }
}

// Schedule daily cleanup at 2:00 AM
function scheduleCleanup() {
  const now = new Date();
  const next2AM = new Date(now);
  next2AM.setHours(2, 0, 0, 0);
  
  // If 2 AM has passed today, schedule for tomorrow
  if (now > next2AM) {
    next2AM.setDate(next2AM.getDate() + 1);
  }
  
  const timeUntilCleanup = next2AM - now;
  
  setTimeout(() => {
    cleanupExpiredMappings();
    // Schedule next cleanup (24 hours later)
    setInterval(cleanupExpiredMappings, 24 * 60 * 60 * 1000);
  }, timeUntilCleanup);
  
  console.log(`[CLEANUP] Next cleanup scheduled for: ${next2AM.toISOString()}`);
}

// Start cleanup scheduler when server starts
scheduleCleanup();
```

#### server.js - Expiration Check in Redirect

```javascript
// In the redirect handler, check expiration
app.get('/:shortId', (req, res) => {
  const shortId = req.params.shortId;
  const mappings = loadUrlMappings();
  const mapping = mappings[shortId];
  
  if (mapping) {
    // Check if link has expired
    const now = Date.now();
    if (mapping.expiresAt && now > mapping.expiresAt) {
      console.log(`[EXPIRED] Short URL ${shortId} has expired`);
      return res.status(410).send('This link has expired');
    }
    
    // Update access tracking
    mapping.clicks = (mapping.clicks || 0) + 1;
    mapping.lastAccessed = now;
    saveUrlMappings(mappings);
    
    // Redirect to long URL
    res.redirect(mapping.longUrl);
  } else {
    res.status(404).send('Short URL not found');
  }
});
```

#### generate_sms_links.py - Add Expiration Field

```python
# When creating new URL mapping
created_at = int(time.time() * 1000)  # Current timestamp in milliseconds
expires_at = created_at + (90 * 24 * 60 * 60 * 1000)  # 90 days from now

url_mappings[short_id] = {
    "longUrl": long_url,
    "clicks": 0,
    "createdAt": created_at,
    "expiresAt": expires_at,  # NEW FIELD
    "lastAccessed": None
}
```

## Backward Compatibility

### Handling Old Mappings

Old mappings without `expiresAt` field:
- Cleanup function calculates expiration based on `createdAt + 90 days`
- No data migration required
- Gradual transition as new links are generated

### Migration Strategy

1. Deploy new code (no immediate impact)
2. New links get `expiresAt` field automatically
3. Old links expire based on `createdAt` age
4. First cleanup archives old entries
5. System stabilizes with only recent links

## Expected Impact

### File Size Reduction

**Before Cleanup:**
- 1,000 letters/month × 12 months = 12,000 entries
- Estimated size: ~2.5 MB
- Growing indefinitely

**After Cleanup (90-day retention):**
- Max ~3,000 active entries (3 months of data)
- Estimated size: ~600 KB
- Stable size (doesn't grow beyond 90 days)

### Performance Improvement

- **Load Time**: 75% faster (smaller file to parse)
- **Memory Usage**: 75% reduction
- **Write Operations**: Faster due to smaller file
- **Lookup Speed**: Minimal impact (still O(1) hash lookup)

## Monitoring & Maintenance

### Logs to Monitor

```
[CLEANUP] Next cleanup scheduled for: 2026-02-13T02:00:00.000Z
[CLEANUP] Active: 2847, Expired: 156
[CLEANUP] Archived 156 expired mappings to url_mappings_archive_2026-02-12.json
[EXPIRED] Short URL abc123 has expired
```

### Manual Cleanup Command

If needed, trigger cleanup manually:

```javascript
// In Node.js console or add API endpoint
cleanupExpiredMappings();
```

### Archive Management

**Archive Files:**
- Location: Root directory
- Naming: `url_mappings_archive_YYYY-MM-DD.json`
- Retention: Keep indefinitely (or delete after 1 year if needed)
- Size: Each archive ~100-500 KB depending on monthly volume

**Cleanup Old Archives (optional):**
```bash
# Delete archives older than 1 year
find . -name "url_mappings_archive_*.json" -mtime +365 -delete
```

## Testing Checklist

### Before Deployment

- [ ] Backup current `url_mappings.json`
- [ ] Test cleanup function with sample data
- [ ] Verify archive file creation
- [ ] Test expiration check in redirect handler
- [ ] Verify new links get `expiresAt` field

### After Deployment

- [ ] Monitor first scheduled cleanup (2:00 AM)
- [ ] Verify active mappings file size reduced
- [ ] Check archive file created successfully
- [ ] Test expired link returns 410 status
- [ ] Verify new links work correctly
- [ ] Monitor server logs for errors

### Test Scenarios

1. **New Link Creation**
   - Generate SMS links
   - Verify `expiresAt` field present
   - Confirm expiration is 90 days from creation

2. **Expired Link Access**
   - Manually set `expiresAt` to past date
   - Access short URL
   - Verify 410 "Link has expired" response

3. **Cleanup Execution**
   - Manually trigger cleanup
   - Verify expired entries archived
   - Confirm active entries remain
   - Check archive file created

4. **Backward Compatibility**
   - Test old mappings without `expiresAt`
   - Verify they expire based on `createdAt` age
   - Confirm no errors in logs

## Rollback Plan

If issues occur:

1. **Stop Server:**
   ```bash
   pm2 stop nicl-backend
   ```

2. **Restore Backup:**
   ```bash
   cp url_mappings.json.backup url_mappings.json
   ```

3. **Revert Code:**
   ```bash
   git checkout HEAD~1 server.js generate_sms_links.py
   ```

4. **Restart Server:**
   ```bash
   pm2 start nicl-backend
   ```

## Future Enhancements

### Phase 2 (Optional)

1. **Database Migration**
   - Move from JSON to SQLite/PostgreSQL
   - Better performance at scale
   - Advanced querying capabilities

2. **Configurable Expiration**
   - Allow different expiration periods per link type
   - Admin UI to adjust expiration settings

3. **Link Renewal**
   - API endpoint to extend expiration
   - Automatic renewal for frequently accessed links

4. **Analytics Dashboard**
   - View cleanup statistics
   - Monitor link usage trends
   - Archive search functionality

## Summary

This cleanup system ensures `url_mappings.json` remains small and performant by:
- Automatically expiring links after 90 days
- Archiving old entries for historical reference
- Running daily cleanup at 2:00 AM
- Maintaining backward compatibility with existing links

**Expected Result:** File size stabilizes at ~600 KB with ~3,000 active entries, regardless of total links generated over time.
