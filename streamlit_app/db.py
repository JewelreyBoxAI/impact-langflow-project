"""
Database helper functions for chat thread and message persistence
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations for chat persistence"""
    
    def __init__(self):
        # PostgreSQL configuration
        self.postgres_url = os.getenv("POSTGRES_URL")
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = os.getenv("POSTGRES_PORT", 5432)
        self.postgres_db = os.getenv("POSTGRES_DB", "impact_ai")
        self.postgres_user = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        
        # Initialize connections
        self._init_postgres()
        self._init_redis()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection and create tables if needed"""
        try:
            if self.postgres_url:
                conn = psycopg2.connect(self.postgres_url)
            else:
                conn = psycopg2.connect(
                    host=self.postgres_host,
                    port=self.postgres_port,
                    database=self.postgres_db,
                    user=self.postgres_user,
                    password=self.postgres_password
                )
            
            with conn.cursor() as cur:
                # Create threads table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_threads (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        flow_name VARCHAR(100) NOT NULL,
                        flow_id VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB DEFAULT '{}'::jsonb
                    )
                """)
                
                # Create messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id SERIAL PRIMARY KEY,
                        thread_id VARCHAR(36) REFERENCES chat_threads(id) ON DELETE CASCADE,
                        role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{}'::jsonb,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_thread_id (thread_id),
                        INDEX idx_timestamp (timestamp)
                    )
                """)
                
                conn.commit()
                logger.info("PostgreSQL tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            # For development, we'll continue without PostgreSQL
            logger.warning("Continuing without PostgreSQL - using in-memory storage")
            
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            logger.warning("Continuing without Redis - using in-memory storage")
    
    def _get_postgres_connection(self):
        """Get PostgreSQL connection"""
        try:
            if self.postgres_url:
                return psycopg2.connect(self.postgres_url, cursor_factory=RealDictCursor)
            else:
                return psycopg2.connect(
                    host=self.postgres_host,
                    port=self.postgres_port,
                    database=self.postgres_db,
                    user=self.postgres_user,
                    password=self.postgres_password,
                    cursor_factory=RealDictCursor
                )
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL connection: {str(e)}")
            return None
    
    def create_thread(self, thread_data: Dict[str, Any]) -> bool:
        """Create a new chat thread"""
        conn = self._get_postgres_connection()
        if not conn:
            logger.warning("No PostgreSQL connection - thread not persisted")
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_threads (id, name, flow_name, flow_id, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    thread_data["id"],
                    thread_data["name"],
                    thread_data["flow_name"],
                    thread_data["flow_id"],
                    thread_data["created_at"],
                    json.dumps(thread_data.get("metadata", {}))
                ))
                conn.commit()
                logger.info(f"Created thread {thread_data['id']}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create thread: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_user_threads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's chat threads"""
        conn = self._get_postgres_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, flow_name, flow_id, created_at, updated_at, metadata
                    FROM chat_threads
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (limit,))
                
                threads = []
                for row in cur.fetchall():
                    threads.append({
                        "id": row["id"],
                        "name": row["name"],
                        "flow_name": row["flow_name"],
                        "flow_id": row["flow_id"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "metadata": row["metadata"]
                    })
                
                return threads
                
        except Exception as e:
            logger.error(f"Failed to get threads: {str(e)}")
            return []
        finally:
            conn.close()
    
    def save_message(self, message_data: Dict[str, Any]) -> bool:
        """Save a chat message"""
        conn = self._get_postgres_connection()
        if not conn:
            logger.warning("No PostgreSQL connection - message not persisted")
            return False
        
        try:
            with conn.cursor() as cur:
                # Save message
                cur.execute("""
                    INSERT INTO chat_messages (thread_id, role, content, metadata, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    message_data["thread_id"],
                    message_data["role"],
                    message_data["content"],
                    json.dumps(message_data.get("metadata", {})),
                    message_data["timestamp"]
                ))
                
                # Update thread updated_at
                cur.execute("""
                    UPDATE chat_threads 
                    SET updated_at = %s 
                    WHERE id = %s
                """, (message_data["timestamp"], message_data["thread_id"]))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save message: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get messages for a specific thread"""
        conn = self._get_postgres_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT role, content, metadata, timestamp
                    FROM chat_messages
                    WHERE thread_id = %s
                    ORDER BY timestamp ASC
                """, (thread_id,))
                
                messages = []
                for row in cur.fetchall():
                    messages.append({
                        "role": row["role"],
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "timestamp": row["timestamp"]
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get messages for thread {thread_id}: {str(e)}")
            return []
        finally:
            conn.close()
    
    def clear_all_threads(self) -> bool:
        """Clear all threads and messages (for development)"""
        conn = self._get_postgres_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_messages")
                cur.execute("DELETE FROM chat_threads")
                conn.commit()
                logger.info("All threads and messages cleared")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear threads: {str(e)}")
            return False
        finally:
            conn.close()
    
    def cache_get(self, key: str) -> Optional[str]:
        """Get value from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None
    
    def cache_set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set value in Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.setex(key, expire, value)
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False