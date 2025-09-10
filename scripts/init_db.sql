-- AI Crawler Assistant 数据库初始化脚本

-- 设置数据库编码
SET client_encoding = 'UTF8';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建数据库用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'crawler_user') THEN
        CREATE USER crawler_user WITH PASSWORD 'crawler_password';
    END IF;
END
$$;

-- 授权
GRANT ALL PRIVILEGES ON DATABASE crawler_db TO crawler_user;

-- 创建索引函数
CREATE OR REPLACE FUNCTION create_indexes()
RETURNS void AS $$
BEGIN
    -- 在表创建后添加索引
    -- 这些索引将在Alembic迁移中正式创建
    NULL;
END;
$$ LANGUAGE plpgsql;

-- 创建清理函数
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- 清理30天前的日志
    DELETE FROM crawl_logs 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- 清理60天前的失败会话
    DELETE FROM crawl_sessions 
    WHERE status = 'failed' 
    AND created_at < NOW() - INTERVAL '60 days';
    
    RAISE NOTICE '数据清理完成';
END;
$$ LANGUAGE plpgsql;

-- 创建统计函数
CREATE OR REPLACE FUNCTION get_crawl_statistics()
RETURNS TABLE(
    total_sessions bigint,
    successful_sessions bigint,
    failed_sessions bigint,
    total_jobs bigint,
    success_rate numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_sessions,
        COUNT(*) FILTER (WHERE status = 'completed') as successful_sessions,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_sessions,
        COALESCE(SUM(jobs_saved), 0) as total_jobs,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND(COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*), 2)
            ELSE 0
        END as success_rate
    FROM crawl_sessions;
END;
$$ LANGUAGE plpgsql;

-- 创建数据库配置
COMMENT ON DATABASE crawler_db IS 'AI Crawler Assistant 数据库';

-- 设置时区
SET timezone = 'Asia/Shanghai';

