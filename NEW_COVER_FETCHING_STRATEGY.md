# New Cover Fetching Strategy

## 🎯 Strategy Overview

**Primary Goal**: Fetch high-quality cover images for remaining 240 series without MangaDex

### 🔄 New Source Strategy:
1. **Google Books API** (Primary)
   - High quality English edition covers
   - Official publisher images
   - Best for mainstream manga

2. **Gemini 2.5 Flash Lite Web Search** (Secondary)
   - Intelligent image search
   - Context-aware cover identification
   - Good for obscure series

3. **DeepSeek Web Search** (Tertiary)
   - Fallback image search
   - Alternative perspective
   - Redundancy for difficult cases

### 🚫 Removed Source:
- **MangaDex**: Removed due to placeholder images from bot detection

## 📊 Rate Limit Strategy

### Conservative Limits (90% of known limits):

| Source | Known Limit | Our Limit | Requests/Second |
|--------|-------------|-----------|-----------------|
| **Google Books** | 1000/day | 900/day | ~0.01/sec |
| **Gemini** | 1500/min | 1350/min | ~22/sec |
| **DeepSeek** | 1000/min | 900/min | ~15/sec |

### Implementation:
- **Google Books**: 1 second between requests
- **Gemini**: 0.044 seconds between requests
- **DeepSeek**: 0.067 seconds between requests

## 🛠️ Implementation Details

### Files Created:

1. **`enhanced_cover_fetcher.py`**
   - Multi-source fallback implementation
   - Rate limiting and statistics tracking
   - URL validation

2. **`fix_cover_images_enhanced.py`**
   - Updated cover fixing script
   - Popular series prioritization
   - Progress tracking and reporting

### Key Features:

#### 1. **Intelligent Prioritization**
```sql
ORDER BY
    CASE
        WHEN series_name IN ('One Piece', 'Naruto', ...) THEN 1
        WHEN total_volumes > 20 THEN 2
        WHEN publisher IS NOT NULL THEN 3
        ELSE 4
    END
```

#### 2. **Multi-Source Fallback**
```python
fetchers = [
    GoogleBooksCoverFetcher(),      # Primary
    GeminiWebSearchFetcher(),       # Secondary
    DeepSeekWebSearchFetcher()      # Tertiary
]
```

#### 3. **Quality Validation**
- HTTP HEAD requests to verify accessibility
- Content-type checking for images
- URL format validation

## 📈 Expected Performance

### Success Rate Projections:
- **Google Books**: ~70% success rate for mainstream manga
- **Gemini Web Search**: ~50% success rate for obscure series
- **DeepSeek Web Search**: ~40% success rate as fallback
- **Overall**: ~80% success rate expected

### Processing Speed:
- **100 series per batch** (increased from 20)
- **~2-3 minutes per series** (with fallbacks)
- **~4-5 hours for full batch** of 100 series

## 🎯 Immediate Action Plan

### Phase 1: Initial Batch (Today)
1. Run `fix_cover_images_enhanced.py`
2. Process 100 popular series first
3. Target: 70-80 successful covers
4. Time: ~4-5 hours

### Phase 2: Remaining Series (Tomorrow)
1. Process next 100 series
2. Target: Additional 60-70 covers
3. Focus on medium-priority series

### Phase 3: Difficult Cases (Day 3)
1. Process final 40 series
2. Manual intervention for stubborn cases
3. Target: Final 20-30 covers

## 🔧 Technical Implementation Notes

### Google Books API Integration:
- Searches for `"{series_name}" "volume 1" manga`
- Prioritizes volume-specific covers
- Uses image size hierarchy (extraLarge → smallThumbnail)

### Web Search Implementation:
- **Placeholder currently** - needs actual API integration
- Will use existing VertexAIAPI and DeepSeekAPI classes
- Web search prompts optimized for cover image discovery

### Error Handling:
- Graceful degradation between sources
- Detailed error logging
- Statistics tracking for optimization

## 📊 Monitoring & Optimization

### Success Tracking:
- Success rates by source
- Processing time per series
- Quality metrics for covers

### Optimization Opportunities:
1. **Query Optimization**: Better search terms for difficult series
2. **Source Weighting**: Adjust source order based on success rates
3. **Batch Size Tuning**: Optimize for API limits and processing time

## 🚀 Quick Start

### Run Enhanced Script:
```bash
python3 fix_cover_images_enhanced.py
```

### Expected Output:
- Progress indicators for each series
- Success/failure counts
- Detailed statistics by source
- Remaining work calculation

## 💡 Key Advantages

1. **Higher Quality**: Google Books provides official publisher images
2. **Better Coverage**: Multiple sources handle different types of manga
3. **Rate Limit Compliant**: Conservative limits prevent API issues
4. **Progress Tracking**: Clear metrics for monitoring completion
5. **Quality Validation**: Ensures covers are accessible and relevant

This new strategy should significantly improve both the success rate and quality of cover image fetching while avoiding the placeholder image issues from MangaDex.