-- MySQL initialization script
-- This runs when the MySQL container is first created

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS blog_db;

USE blog_db;

-- Drop and recreate the table (CAUTION: This deletes all data)
DROP TABLE IF EXISTS blog_posts;

-- Create blog_posts table with HITL fields
CREATE TABLE IF NOT EXISTS blog_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL UNIQUE,
    topic VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_at DATETIME NULL,
    rejection_reason TEXT NULL,
    INDEX idx_thread_id (thread_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data (optional, for testing)
-- INSERT INTO blog_posts (thread_id, topic, title, content, status) VALUES
-- ('blog_sample001', 'Sample Topic', 'Sample Blog Title', 'This is sample content.', 'approved');

-- Verify the table structure
DESCRIBE blog_posts;

-- Grant privileges to blog_user
GRANT ALL PRIVILEGES ON blog_db.* TO 'blog_user'@'%';
FLUSH PRIVILEGES;
