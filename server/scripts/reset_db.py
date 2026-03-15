"""
Reset database script - WARNING: Deletes all data!
"""

import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def reset_database():
    """Reset the database (WARNING: Deletes all data!)"""
    db_path = Path(__file__).parent.parent / 'data' / 'neighborhood.db'
    
    if db_path.exists():
        response = input(f"⚠️  This will DELETE all data in {db_path}\nAre you sure? (yes/no): ")
        
        if response.lower() == 'yes':
            os.remove(db_path)
            print(f"✓ Deleted {db_path}")
            
            # Reinitialize
            from models import db
            db.init_db()
            print("✓ Database reinitialized")
            print("\n✅ Database reset complete!")
        else:
            print("Operation cancelled.")
    else:
        print(f"Database not found at {db_path}")

if __name__ == '__main__':
    reset_database()
