"""
Hardware-only logging system for Neighborhood BBS
Logs only hardware/system events, no user data
"""

import logging
from pathlib import Path
from datetime import datetime
import json

# Log directory
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Hardware log file
HARDWARE_LOG_FILE = LOG_DIR / 'hardware.log'


class HardwareOnlyFormatter(logging.Formatter):
    """Formatter for hardware-only logs (no user data)"""
    
    def format(self, record):
        """Format log record without sensitive data"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'event': record.msg,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Only include specific attributes, never user data
        if hasattr(record, 'hardware_info'):
            log_entry['hardware'] = record.hardware_info
        
        return json.dumps(log_entry)


def setup_hardware_logger():
    """Setup hardware-only logger"""
    logger = logging.getLogger('bbs_hardware')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers = []
    
    # File handler for hardware logs
    file_handler = logging.FileHandler(HARDWARE_LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(HardwareOnlyFormatter())
    logger.addHandler(file_handler)
    
    return logger


# Global logger
hardware_logger = setup_hardware_logger()


def log_hardware_event(event, **kwargs):
    """Log hardware/system event only"""
    record = logging.LogRecord(
        name='bbs_hardware',
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=event,
        args=tuple(),
        exc_info=None
    )
    record.hardware_info = kwargs
    hardware_logger.handle(record)


def log_system_startup(host, port, connections):
    """Log system startup"""
    log_hardware_event('system_startup', host=host, port=port, max_connections=connections)


def log_connection_attempt(ip_address, result='success'):
    """Log connection attempt (IP only, no user data)"""
    log_hardware_event('connection_attempt', ip=ip_address, result=result)


def log_connection_closed(ip_address, duration_seconds=None):
    """Log connection closed"""
    log_hardware_event('connection_closed', ip=ip_address, duration=duration_seconds)


def log_rate_limit_exceeded(ip_address, endpoint):
    """Log rate limit exceeded"""
    log_hardware_event('rate_limit_exceeded', ip=ip_address, endpoint=endpoint)


def log_device_banned(device_id, reason):
    """Log device ban"""
    log_hardware_event('device_banned', device_id=device_id, reason=reason)


def log_device_unbanned(device_id):
    """Log device unban"""
    log_hardware_event('device_unbanned', device_id=device_id)


def log_config_changed(setting_name, admin):
    """Log configuration change"""
    log_hardware_event('config_changed', setting=setting_name, admin=admin)


def log_theme_changed(theme_name, admin):
    """Log theme change"""
    log_hardware_event('theme_changed', theme=theme_name, admin=admin)


def log_cpu_usage(percent):
    """Log CPU usage"""
    log_hardware_event('cpu_usage', percent=percent)


def log_memory_usage(percent):
    """Log memory usage"""
    log_hardware_event('memory_usage', percent=percent)


def log_disk_usage(percent):
    """Log disk usage"""
    log_hardware_event('disk_usage', percent=percent)


def log_network_io(bytes_sent, bytes_recv):
    """Log network I/O"""
    log_hardware_event('network_io', bytes_sent=bytes_sent, bytes_received=bytes_recv)


def get_hardware_logs(limit=100):
    """Read hardware logs"""
    if not HARDWARE_LOG_FILE.exists():
        return []
    
    logs = []
    with open(HARDWARE_LOG_FILE, 'r') as f:
        for line in f.readlines()[-limit:]:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    return logs
