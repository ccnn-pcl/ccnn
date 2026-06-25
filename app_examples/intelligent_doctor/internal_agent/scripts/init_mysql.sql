-- MySQL数据库初始化脚本
-- ================================

-- 使用数据库（需要在创建数据库后执行）
-- CREATE DATABASE IF NOT EXISTS private_doctor_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE private_doctor_db;

-- 1. 用户认证表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'patient',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 用户档案表
CREATE TABLE IF NOT EXISTS user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    full_name VARCHAR(200),
    phone VARCHAR(20),
    address TEXT,
    birth_date DATE,
    gender VARCHAR(10),
    emergency_contact VARCHAR(200),
    allergies JSON,
    medications JSON,
    medical_conditions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_profiles_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 聊天历史表
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    agent_name VARCHAR(100),
    round_number INT,
    metadata JSON,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_chat_history_user_id (user_id),
    INDEX idx_chat_history_timestamp (timestamp),
    INDEX idx_chat_history_session_id (session_id),
    INDEX idx_chat_history_round_number (round_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 医疗影像表
CREATE TABLE IF NOT EXISTS medical_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    hospital_id VARCHAR(50) NOT NULL,
    image_data LONGBLOB,
    image_type VARCHAR(50) NOT NULL,
    image_category VARCHAR(50) NOT NULL,
    examination_date DATE NOT NULL,
    description TEXT,
    filename VARCHAR(255),
    file_size INT,
    file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_medical_images_user_id (user_id),
    INDEX idx_medical_images_hospital_id (hospital_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 医疗记录表
CREATE TABLE IF NOT EXISTS medical_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    hospital_id VARCHAR(50) NOT NULL,
    record_data TEXT NOT NULL,
    record_type VARCHAR(50) NOT NULL,
    description TEXT,
    filename VARCHAR(255),
    file_size INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_medical_records_user_id (user_id),
    INDEX idx_medical_records_hospital_id (hospital_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 医院信息表
CREATE TABLE IF NOT EXISTS hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id VARCHAR(50) UNIQUE NOT NULL,
    hospital_name VARCHAR(200) NOT NULL,
    location VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(500),
    database_storage_endpoint VARCHAR(500),
    model_config JSON,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    granted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. 用户活动表
CREATE TABLE IF NOT EXISTS user_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. 体征数据表
CREATE TABLE IF NOT EXISTS user_vitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    systolic_pressure INT,
    diastolic_pressure INT,
    heart_rate INT,
    temperature DECIMAL(4,1),
    weight DECIMAL(5,2),
    height DECIMAL(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 重构新增表（智能体重构方案 v2.0）
-- ============================================================

-- 11. 诊断会话表（必需）- 存储多轮协调的诊断会话状态
CREATE TABLE IF NOT EXISTS diagnosis_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    intent VARCHAR(50),
    status VARCHAR(20) DEFAULT 'in_progress',
    current_round INT DEFAULT 0,
    max_rounds INT DEFAULT 5,
    shared_context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_diagnosis_sessions_user_id (user_id),
    INDEX idx_diagnosis_sessions_session_id (session_id),
    INDEX idx_diagnosis_sessions_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. 诊断结果缓存表（必需）- 缓存诊断结果，不存储原始医疗数据
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    round_number INT NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    location VARCHAR(50),
    diagnosis_summary TEXT,
    confidence DECIMAL(3,2),
    data_requirements JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES diagnosis_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_diagnosis_results_session_id (session_id),
    INDEX idx_diagnosis_results_round_number (round_number),
    INDEX idx_diagnosis_results_agent_name (agent_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. 数据地址历史表（推荐保留）- 记录获取的数据地址，不存储实际数据
CREATE TABLE IF NOT EXISTS data_address_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    round_number INT NOT NULL,
    data_addresses JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES diagnosis_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_data_address_history_session_id (session_id),
    INDEX idx_data_address_history_round_number (round_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. 综合诊断报告表（必需）- 存储最终生成的综合诊断报告
CREATE TABLE IF NOT EXISTS comprehensive_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    report_content TEXT NOT NULL,
    evolution_summary JSON,
    specialist_results JSON,
    total_rounds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES diagnosis_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_comprehensive_reports_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认医院数据
INSERT INTO hospitals (hospital_id, hospital_name, location, status) VALUES
('BJ001', '北京医院', '北京', 'active'),
('SH001', '上海医院', '上海', 'active'),
('TEST001', '测试医院', '测试城市', 'active')
ON DUPLICATE KEY UPDATE
    hospital_name = VALUES(hospital_name),
    location = VALUES(location),
    status = VALUES(status);

-- 插入默认权限数据
INSERT INTO permissions (role, resource, action, granted) VALUES
('patient', 'medical_records', 'read', TRUE),
('patient', 'medical_images', 'read', TRUE),
('patient', 'chat_history', 'read', TRUE),
('patient', 'chat_history', 'write', TRUE),
('doctor', 'medical_records', 'read', TRUE),
('doctor', 'medical_records', 'write', TRUE),
('doctor', 'medical_images', 'read', TRUE),
('doctor', 'medical_images', 'write', TRUE),
('doctor', 'chat_history', 'read', TRUE),
('doctor', 'chat_history', 'write', TRUE),
('admin', '*', '*', TRUE)
ON DUPLICATE KEY UPDATE
    granted = VALUES(granted);

-- 完成提示
SELECT 'MySQL数据库初始化完成！' as message;

