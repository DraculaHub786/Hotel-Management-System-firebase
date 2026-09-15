import random
import time
import logging
from datetime import datetime, timedelta
import bcrypt
from app.firebase_db import otp_codes_col

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5

def hash_otp(code: str) -> str:
    """Hash OTP using bcrypt"""
    return bcrypt.hashpw(code.encode('utf-8'), bcrypt.gensalt(rounds=10)).decode('utf-8')

def check_otp_hash(code: str, hashed: str) -> bool:
    """Verify OTP against bcrypt hash"""
    try:
        return bcrypt.checkpw(code.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def generate_and_store_otp(email: str, purpose: str = 'register') -> str:
    """
    Generates a 6-digit numeric OTP, bcrypt-hashes it, and stores it in Firestore otp_codes collection.
    Fulfills master_plan.md Module 1 / Phase 2 specification.
    """
    email = email.lower().strip()
    code = f"{random.randint(100000, 999999)}"
    code_hash = hash_otp(code)
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    col = otp_codes_col()
    
    # Invalidate any prior active OTPs for this email and purpose
    try:
        prior_docs = col.where('email', '==', email).where('purpose', '==', purpose).stream()
        for doc in prior_docs:
            doc.reference.delete()
    except Exception as e:
        logger.warning(f"Failed to clear old OTPs for {email}: {e}")
        
    otp_doc = {
        "email": email,
        "code_hash": code_hash,
        "purpose": purpose,
        "attempts": 0,
        "expires_at": expires_at.isoformat() + "Z",
        "created_at": now.isoformat() + "Z"
    }
    
    try:
        col.add(otp_doc)
        logger.info(f"🔑 OTP generated for {email} [{purpose}]: {code} (expires in {OTP_EXPIRY_MINUTES}m)")
    except Exception as e:
        logger.error(f"Failed to store OTP in Firestore: {e}")
        
    return code

def verify_otp(email: str, code: str, purpose: str = 'register') -> tuple[bool, str]:
    """
    Verifies the OTP against the stored bcrypt hash with 5-min expiry and max 5 attempts.
    """
    email = email.lower().strip()
    code = str(code).strip()
    col = otp_codes_col()
    
    try:
        docs = list(col.where('email', '==', email).where('purpose', '==', purpose).limit(1).get())
        if not docs:
            return False, "No active OTP request found. Please request a new code."
            
        doc = docs[0]
        data = doc.to_dict()
        
        # Check attempts
        attempts = data.get('attempts', 0)
        if attempts >= MAX_OTP_ATTEMPTS:
            doc.reference.delete()
            return False, "Maximum verification attempts exceeded. Please request a new OTP."
            
        # Check expiry
        expires_str = data.get('expires_at', '')
        try:
            exp_clean = expires_str.replace('Z', '')
            exp_time = datetime.fromisoformat(exp_clean)
            if datetime.utcnow() > exp_time:
                doc.reference.delete()
                return False, "OTP has expired. Please request a new one."
        except Exception:
            pass
            
        # Check hash
        code_hash = data.get('code_hash', '')
        if check_otp_hash(code, code_hash):
            doc.reference.delete()
            return True, "OTP verified successfully."
        else:
            # Increment attempt counter
            new_attempts = attempts + 1
            doc.reference.update({'attempts': new_attempts})
            rem = MAX_OTP_ATTEMPTS - new_attempts
            return False, f"Invalid OTP. {rem} attempt(s) remaining."
    except Exception as e:
        logger.error(f"Error during OTP verification: {e}")
        return False, "An error occurred during verification."
