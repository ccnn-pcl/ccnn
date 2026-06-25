-- 迁移 user_manager.py 到 MySQL 所需的表结构更新
-- ============================================================

-- 1. 更新 user_profiles 表，添加缺失的字段
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS avatar TEXT,
ADD COLUMN IF NOT EXISTS preferences JSON;

-- 注意：如果 avatar 和 preferences 字段已存在，上面的语句会报错，可以忽略

-- 2. 创建 user_preferences 表（如果不存在）
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    language VARCHAR(10) DEFAULT 'zh-CN',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    theme VARCHAR(20) DEFAULT 'light',
    notifications JSON,
    privacy_settings JSON,
    display_settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_preferences_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 更新 user_activities 表，添加缺失的字段
ALTER TABLE user_activities
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45),
ADD COLUMN IF NOT EXISTS user_agent TEXT,
ADD COLUMN IF NOT EXISTS metadata JSON,
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 注意：如果字段已存在，上面的语句会报错，可以忽略

-- 4. 创建 user_data_stats 表
CREATE TABLE IF NOT EXISTS user_data_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    total_chat_messages INT DEFAULT 0,
    total_medical_images INT DEFAULT 0,
    total_medical_records INT DEFAULT 0,
    last_activity TIMESTAMP NULL,
    data_usage_mb DECIMAL(10,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_data_stats_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 创建 user_subscriptions 表
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    subscription_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    start_date TIMESTAMP NULL,
    end_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, service_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_subscriptions_user_id (user_id),
    INDEX idx_user_subscriptions_service_name (service_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 完成提示
SELECT 'user_manager.py 表结构迁移完成！' as message;

