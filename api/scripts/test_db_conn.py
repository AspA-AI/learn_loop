import socket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dns():
    host = "db.wkjjfqhkiwqersozobuk.supabase.co"
    port = 5432
    logger.info(f"Attempting to resolve {host}...")
    try:
        ip = socket.gethostbyname(host)
        logger.info(f"Successfully resolved {host} to {ip}")
        
        logger.info(f"Attempting to connect to {ip}:{port}...")
        s = socket.create_connection((ip, port), timeout=5)
        logger.info("Successfully connected!")
        s.close()
    except Exception as e:
        logger.error(f"DNS or Connection failed: {e}")

if __name__ == "__main__":
    test_dns()

