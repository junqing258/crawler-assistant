-- AI Crawler Assistant MySQL数据库初始化脚本

-- 设置字符集和排序规则
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS crawler_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE crawler_db;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'crawler_user'@'%' IDENTIFIED BY 'crawler_password';

-- 授权
GRANT ALL PRIVILEGES ON crawler_db.* TO 'crawler_user'@'%';
FLUSH PRIVILEGES;

-- 创建清理函数
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS cleanup_old_data()
BEGIN
    -- 清理30天前的日志
    DELETE FROM crawl_logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- 清理60天前的失败会话
    DELETE FROM crawl_sessions 
    WHERE status = 'failed' 
    AND created_at < DATE_SUB(NOW(), INTERVAL 60 DAY);
    
    SELECT 'Data cleanup completed' as message;
END //

DELIMITER ;

-- 创建统计函数
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS get_crawl_statistics()
BEGIN
    SELECT 
        COUNT(*) as total_sessions,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_sessions,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_sessions,
        COALESCE(SUM(jobs_saved), 0) as total_jobs,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
            ELSE 0
        END as success_rate
    FROM crawl_sessions;
END //

DELIMITER ;

-- 设置MySQL配置
SET GLOBAL innodb_file_format = 'Barracuda';
SET GLOBAL innodb_file_per_table = ON;
SET GLOBAL innodb_large_prefix = ON;

-- 数据库注释
ALTER DATABASE crawler_db COMMENT = 'AI Crawler Assistant Database';

-- 设置时区
SET time_zone = '+08:00';
