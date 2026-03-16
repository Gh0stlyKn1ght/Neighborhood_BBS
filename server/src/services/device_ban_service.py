"""
Device-based banning service for Neighborhood BBS
Handles MAC address detection, hashing, and device-level bans
Week 7 Implementation
"""

import hashlib
import json
import socket
import subprocess
import logging
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Tuple
from flask import request
from models import BannedDevice

logger = logging.getLogger(__name__)

# Global instance
_device_ban_service_instance = None
_instance_lock = Lock()


class DeviceBanService:
    """
    Device-based ban enforcement for escalation (persistent abusers).
    
    Design Principles:
    - Extract device identifier from connection (IP + User-Agent)
    - Attempt to retrieve MAC address for better device identification
    - Hash MAC for privacy (never store plain)
    - Check device bans on WebSocket connect event
    - Enforce hard block for banned devices (last resort)
    - Auto-expire bans after configured duration
    - Support admin override to ban/unban
    
    Architecture:
    - _device_ids: Cache of (ip, user_agent) → device_id mappings
    - check_device_allowed(): Called on connect, returns (allowed, reason, device_info)
    - ban_device(): Admin action to ban (usually after repeated session mutes)
    - unban_device(): Admin action to restore access
    - get_device_info(): Retrieve current device info from request
    """
    
    def __init__(self):
        """Initialize DeviceBanService with empty cache"""
        self._device_ids = {}  # Cache (ip, user_agent) → device_id
        self._mac_cache = {}   # Cache ip → mac_address
        self._device_lock = Lock()
        
    def get_device_info(self) -> Tuple[str, Optional[str], str]:
        """
        Extract device information from current Flask request context.
        
        Returns:
            Tuple of (device_id, mac_address_or_none, ip_address)
            device_id: Hash-based identifier (IP + User-Agent)
            mac_address: Hashed MAC if available, None otherwise
            ip_address: Client IP address
            
        Privacy Note:
            - device_id created from IP + User-Agent (not stored plain)
            - MAC hashed with SHA256 before use (no plain MAC stored)
            - No user/nickname linked to device_id
        """
        try:
            # Get client IP address (respect X-Forwarded-For for proxies)
            if request.headers.get('X-Forwarded-For'):
                ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            else:
                ip_address = request.remote_addr or '127.0.0.1'
            
            # Get user agent for device fingerprinting
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            # Create device_id from IP + User-Agent combination
            device_id = self._create_device_id(ip_address, user_agent)
            
            # Try to get MAC address (best effort)
            mac_address = self._get_mac_address(ip_address)
            
            return device_id, mac_address, ip_address
            
        except Exception as e:
            logger.warning(f"Error extracting device info: {e}")
            # Fallback: use just IP
            ip_address = request.remote_addr or '127.0.0.1'
            device_id = hashlib.sha256(ip_address.encode()).hexdigest()[:16]
            return device_id, None, ip_address
    
    def check_device_allowed(self) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if device is allowed to connect (called on WebSocket connect).
        
        Returns:
            Tuple of (allowed, reason, device_info)
            allowed: True if device can connect, False if banned
            reason: String reason if banned (admin can see in logs)
            device_info: Dict with device identification info for logging
            
        Design:
            - If device banned: return (False, ban_reason, device_info)
            - If not banned: return (True, None, device_info)
            - Check expiration: auto-allow if ban expired
            - No user/nickname linked to ban decision (privacy-first)
        """
        try:
            device_id, mac_address, ip_address = self.get_device_info()
            
            device_info = {
                'device_id': device_id,
                'ip_address': ip_address,
                'mac_hashed': mac_address is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check if device is banned by device_id
            ban = BannedDevice.get_by_device_id(device_id)
            if ban:
                # Check if ban has expired
                if ban.get('expires_at'):
                    try:
                        expires = datetime.fromisoformat(ban['expires_at'])
                        if datetime.now() > expires:
                            # Ban expired - auto-unban
                            BannedDevice.unban_device(device_id)
                            logger.info(f"Auto-unbanned device {device_id} (ban expired)")
                            device_info['ban_status'] = 'expired'
                            return True, None, device_info
                    except Exception as e:
                        logger.warning(f"Error checking ban expiration: {e}")
                
                device_info['ban_status'] = 'active'
                device_info['ban_reason'] = ban.get('ban_reason', 'Banned by admin')
                device_info['banned_at'] = ban.get('banned_at')
                return False, ban.get('ban_reason', 'Device banned'), device_info
            
            # Check if IP address is banned
            ban_by_ip = BannedDevice.get_by_ip(ip_address)
            if ban_by_ip:
                # Check if ban has expired
                if ban_by_ip.get('expires_at'):
                    try:
                        expires = datetime.fromisoformat(ban_by_ip['expires_at'])
                        if datetime.now() > expires:
                            BannedDevice.unban_device(ban_by_ip['device_id'])
                            logger.info(f"Auto-unbanned device {ban_by_ip['device_id']} (ban expired)")
                            return True, None, device_info
                    except Exception as e:
                        logger.warning(f"Error checking IP ban expiration: {e}")
                
                device_info['ban_status'] = 'active_by_ip'
                device_info['ban_reason'] = ban_by_ip.get('ban_reason', 'Banned by admin')
                return False, ban_by_ip.get('ban_reason', 'Device banned'), device_info
            
            # Device not banned
            device_info['ban_status'] = 'allowed'
            return True, None, device_info
            
        except Exception as e:
            logger.error(f"Error checking device ban: {e}")
            # Fail open on errors (allow connection)
            return True, None, {'error': str(e)}
    
    def ban_device(self, device_id: str, device_type: str = 'unknown', 
                   mac_address: Optional[str] = None, ip_address: Optional[str] = None,
                   ban_reason: str = 'Escalation ban', banned_by: str = 'admin',
                   expire_hours: Optional[int] = None) -> bool:
        """
        Ban a device (admin action for persistent abuse).
        
        Args:
            device_id: Device identifier to ban
            device_type: Type of device (browser, phone, etc) - for admin reference
            mac_address: MAC address if available (will be hashed)
            ip_address: IP address if available
            ban_reason: Human-readable reason for ban
            banned_by: Admin username who performed the ban
            expire_hours: Optional expiration (None = permanent)
            
        Returns:
            True if ban successful, False otherwise
            
        Privacy Note:
            - MAC address hashed before storage
            - Ban is device-level, not user/nickname level
            - No tracking of user behavior across devices
        """
        try:
            # Hash MAC if provided
            hashed_mac = None
            if mac_address:
                hashed_mac = hashlib.sha256(mac_address.encode()).hexdigest()
            
            # Calculate expiration
            expires_at = None
            if expire_hours:
                expires_at = (datetime.now() + timedelta(hours=expire_hours)).isoformat()
            
            # Insert ban
            ban_id = BannedDevice.ban_device(
                device_id=device_id,
                device_type=device_type,
                mac_address=hashed_mac,
                ip_address=ip_address,
                ban_reason=ban_reason,
                banned_by=banned_by,
                expires_at=expires_at
            )
            
            if ban_id:
                logger.info(f"Banned device {device_id}: {ban_reason} (by {banned_by}, expires: {expires_at})")
                return True
            else:
                logger.warning(f"Failed to ban device {device_id} (already banned or DB error)")
                return False
                
        except Exception as e:
            logger.error(f"Error banning device: {e}")
            return False
    
    def unban_device(self, device_id: str, unbanned_by: str = 'admin') -> bool:
        """
        Unban a device (admin action for second chance).
        
        Args:
            device_id: Device identifier to unban
            unbanned_by: Admin username who performed the unban
            
        Returns:
            True if unban successful, False otherwise
        """
        try:
            BannedDevice.unban_device(device_id)
            logger.info(f"Unbanned device {device_id} (by {unbanned_by})")
            return True
        except Exception as e:
            logger.error(f"Error unbanning device: {e}")
            return False
    
    def get_active_bans(self) -> list:
        """
        Get list of all active device bans.
        
        Returns:
            List of ban records (including expired ones if not yet cleaned)
            
        Design:
            - Only returns active bans
            - Automatically filters by is_active flag
            - Admin can use to review escalations
        """
        try:
            return BannedDevice.get_all_bans(active_only=True)
        except Exception as e:
            logger.error(f"Error getting active bans: {e}")
            return []
    
    def cleanup_expired_bans(self) -> int:
        """
        Clean up any expired device bans (run periodically).
        
        Returns:
            Number of bans cleaned up
            
        Design:
            - Should be called periodically (e.g., every 30 minutes)
            - Deactivates bans where expires_at has passed
            - Logs each cleanup for audit trail
        """
        try:
            count = 0
            all_bans = BannedDevice.get_all_bans(active_only=True)
            
            for ban in all_bans:
                if ban.get('expires_at'):
                    try:
                        expires = datetime.fromisoformat(ban['expires_at'])
                        if datetime.now() > expires:
                            BannedDevice.unban_device(ban['device_id'])
                            count += 1
                            logger.info(f"Auto-expired ban for device {ban['device_id']}")
                    except Exception as e:
                        logger.warning(f"Error processing ban expiration: {e}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired bans: {e}")
            return 0
    
    # ========== PRIVATE METHODS ==========
    
    def _create_device_id(self, ip_address: str, user_agent: str) -> str:
        """
        Create unique device identifier from IP + User-Agent.
        
        Privacy Design:
            - No plain IP/User-Agent stored
            - Hash created for comparison
            - Consistent within session (same connection = same ID)
            - Changes if user-agent changes (e.g., browser update)
        """
        try:
            cache_key = (ip_address, user_agent)
            if cache_key in self._device_ids:
                return self._device_ids[cache_key]
            
            # Create hash from IP + User-Agent
            combined = f"{ip_address}:{user_agent}"
            device_id = hashlib.sha256(combined.encode()).hexdigest()[:16]
            
            with self._device_lock:
                self._device_ids[cache_key] = device_id
            
            return device_id
        except Exception as e:
            logger.warning(f"Error creating device ID: {e}")
            return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
    
    def _get_mac_address(self, ip_address: str) -> Optional[str]:
        """
        Attempt to retrieve MAC address for device at given IP.
        
        Strategy (try in order):
        1. Check cache first
        2. Use netifaces (cross-platform)
        3. Use ARP table (Linux/Mac)
        4. Use arp command (Windows)
        5. Give up and return None
        
        Returns:
            Hashed MAC address if found, None otherwise
            
        Privacy Note:
            - Returns HASHED MAC (SHA256)
            - Never stores or logs plain MAC
            - Best-effort only - gracefully degrades
        """
        try:
            # Check cache first
            if ip_address in self._mac_cache:
                return self._mac_cache[ip_address]
            
            # Try netifaces (cross-platform)
            try:
                import netifaces
                for interface in netifaces.interfaces():
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr_info in addrs[netifaces.AF_INET]:
                            if addr_info.get('addr') == ip_address:
                                if netifaces.AF_LINK in addrs:
                                    mac = addrs[netifaces.AF_LINK][0].get('addr', '')
                                    if mac:
                                        hashed_mac = hashlib.sha256(mac.encode()).hexdigest()
                                        with self._device_lock:
                                            self._mac_cache[ip_address] = hashed_mac
                                        return hashed_mac
            except ImportError:
                pass
            
            # Try ARP table (Linux/Mac)
            try:
                result = subprocess.run(
                    ['arp', '-n', ip_address],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Parse: "? (192.168.1.1) at 00:11:22:33:44:55"
                    for line in result.stdout.split('\n'):
                        if 'at' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'at' and i + 1 < len(parts):
                                    mac = parts[i + 1]
                                    if self._is_valid_mac(mac):
                                        hashed_mac = hashlib.sha256(mac.encode()).hexdigest()
                                        with self._device_lock:
                                            self._mac_cache[ip_address] = hashed_mac
                                        return hashed_mac
            except Exception:
                pass
            
            # Try Windows ARP
            try:
                result = subprocess.run(
                    ['arp', '-a'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ip_address in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if self._is_valid_mac(part):
                                    hashed_mac = hashlib.sha256(part.encode()).hexdigest()
                                    with self._device_lock:
                                        self._mac_cache[ip_address] = hashed_mac
                                    return hashed_mac
            except Exception:
                pass
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not get MAC for {ip_address}: {e}")
            return None
    
    @staticmethod
    def _is_valid_mac(mac: str) -> bool:
        """Check if string looks like valid MAC address"""
        mac = mac.lower()
        # Format: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        if len(mac) == 17:
            parts = mac.replace('-', ':').split(':')
            if len(parts) == 6:
                try:
                    for part in parts:
                        int(part, 16)
                    return True
                except ValueError:
                    pass
        return False


def get_device_ban_service() -> DeviceBanService:
    """Get or create singleton DeviceBanService instance"""
    global _device_ban_service_instance
    
    if _device_ban_service_instance is None:
        with _instance_lock:
            if _device_ban_service_instance is None:
                _device_ban_service_instance = DeviceBanService()
                logger.info("Initialized DeviceBanService")
    
    return _device_ban_service_instance
