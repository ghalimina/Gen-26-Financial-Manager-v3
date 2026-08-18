import os
import json
import datetime
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

AUTHORITATIVE_SOURCE = os.path.join(DATA_DIR, 'authoritative_paper_sessions.json')

class SessionManager:
    @staticmethod
    def _load():
        if not os.path.exists(AUTHORITATIVE_SOURCE):
            return []
        try:
            with open(AUTHORITATIVE_SOURCE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    @staticmethod
    def _save(sessions):
        with open(AUTHORITATIVE_SOURCE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=4)

    @classmethod
    def start_session(cls, market_date: str):
        """Starts a session. If a successful session already exists for this date, returns None to prevent duplicates."""
        sessions = cls._load()
        
        # 1. Duplicate & Restart Protection (Same Date)
        for s in sessions:
            if s['market_date'] == market_date and s['status'] == 'COMPLETED':
                return None # Already has a valid run today
                
        # 2. Weekend protection (EGX operates Sun-Thu)
        try:
            dt = datetime.datetime.strptime(market_date, "%Y-%m-%d")
            if dt.weekday() >= 5: # 5=Sat, 6=Sun in standard python. EGX is Sun=6, Mon=0, Tue=1, Wed=2, Thu=3. Wait, Friday=4, Saturday=5.
                # So EGX closed Friday(4) and Saturday(5).
                if dt.weekday() in [4, 5]:
                    return None # Closed days don't count
        except:
            pass

        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "market_date": market_date,
            "timezone": "Africa/Cairo",
            "run_timestamp": datetime.datetime.now().isoformat(),
            "status": "STARTED",
            "data_status": "PENDING",
            "paper_mode": True,
            "completion_status": "INCOMPLETE"
        }
        sessions.append(session)
        cls._save(sessions)
        return session_id

    @classmethod
    def complete_session(cls, session_id: str, data_status="VALID"):
        """Marks a session as COMPLETED only if it reaches the end."""
        sessions = cls._load()
        for s in sessions:
            if s['session_id'] == session_id:
                s['status'] = 'COMPLETED'
                s['completion_status'] = 'SUCCESS'
                s['data_status'] = data_status
                break
        cls._save(sessions)

    @classmethod
    def fail_session(cls, session_id: str, reason: str):
        sessions = cls._load()
        for s in sessions:
            if s['session_id'] == session_id:
                s['status'] = 'FAILED'
                s['completion_status'] = reason
                break
        cls._save(sessions)

    @classmethod
    def get_valid_days(cls):
        """Returns the single authoritative count of valid paper days."""
        sessions = cls._load()
        valid_dates = set()
        for s in sessions:
            if s['status'] == 'COMPLETED' and s['completion_status'] == 'SUCCESS':
                valid_dates.add(s['market_date'])
        return len(valid_dates)

    @classmethod
    def inject_fixture(cls, days: int):
        """For boundary testing only."""
        sessions = []
        base_date = datetime.datetime.now()
        for i in range(days):
            d_str = (base_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            sessions.append({
                "session_id": str(uuid.uuid4()),
                "market_date": d_str,
                "timezone": "Africa/Cairo",
                "run_timestamp": datetime.datetime.now().isoformat(),
                "status": "COMPLETED",
                "data_status": "VALID",
                "paper_mode": True,
                "completion_status": "SUCCESS"
            })
        cls._save(sessions)

