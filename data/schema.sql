-- Photos table - core image metadata
CREATE TABLE photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_uuid TEXT UNIQUE NOT NULL,    -- Path in your app storage
    name TEXT NOT NULL,                  -- Display name for searching
    description TEXT,
    file_type TEXT,                      -- 'jpg', 'png', etc.
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    favorite BOOLEAN DEFAULT FALSE,
    checksum TEXT UNIQUE                 -- For duplicate detection
);

-- Albums table - for organizing photos
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- Album name for searching
    description TEXT,
);

-- Tags table - for categorizing photos
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- Tag name for searching
);

-- Many-to-many: Photos can be in multiple albums
CREATE TABLE photo_albums (
    photo_id INTEGER,
    album_id INTEGER,
    PRIMARY KEY (photo_id, album_id),
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

-- Many-to-many: Photos can have multiple tags
CREATE TABLE photo_tags (
    photo_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (photo_id, tag_id),
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);


-- For photo searching
CREATE INDEX idx_photos_date_added ON photos(date_added);       -- sort by date added
CREATE INDEX idx_photos_name ON photos(name);                   -- sort alphabetically

-- For fast duplicate checking
CREATE INDEX idx_photos_checksum ON photos(checksum);

-- For album searching (sorted)
CREATE INDEX idx_albums_name ON albums(name);                   

-- For tag searching (sorted)
CREATE INDEX idx_tags_name ON tags(name);                        

-- For photo searching by tags matching
CREATE INDEX idx_photo_tags_tag_id ON photo_tags(tag_id);       
CREATE INDEX idx_photo_tags_photo_id ON photo_tags(photo_id); 

