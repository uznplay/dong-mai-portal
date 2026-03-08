-- ==============================================================================
-- KEYWORD ALIASES MIGRATION
-- Add keyword_aliases column to featured_news table
-- ==============================================================================

-- Add column
ALTER TABLE featured_news 
ADD COLUMN IF NOT EXISTS keyword_aliases text[] DEFAULT '{}';

-- Add comment
COMMENT ON COLUMN featured_news.keyword_aliases 
IS 'SEO keywords and search aliases for better article discoverability. Example: ["công chứng cccd", "xác nhận bản sao"]';

-- Create GIN index for faster array searches
CREATE INDEX IF NOT EXISTS idx_featured_news_keyword_aliases 
ON featured_news USING GIN (keyword_aliases);

-- Verify column exists
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'featured_news' AND column_name = 'keyword_aliases';
