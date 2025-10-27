-- data/schema.sql
-- Photos table with all columns (final version)
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    album TEXT DEFAULT '',
    tags TEXT,
    description TEXT,
    date_added TEXT,
    favorite INTEGER DEFAULT 0
);

-- Tags lookup table
CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_photos_album ON photos(album);
CREATE INDEX IF NOT EXISTS idx_photos_favorite ON photos(favorite);
CREATE INDEX IF NOT EXISTS idx_photos_date ON photos(date_added);