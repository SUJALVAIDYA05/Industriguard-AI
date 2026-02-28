import requests
import time

class Reporter:
    def __init__(self, backend_url="http://localhost:5000"):
        self.backend_url = backend_url
        print(f"[Reporter] Initialized → backend: {backend_url}")

    def send_check_result(self, employee, status_data, camera_id="CAM-01"):
        """
        Sends completed check result to Flask backend.
        Called once per employee check after PPE analysis is done.
        """
        payload = {
            "employee_id":   employee["id"],
            "employee_name": employee["name"],
            "department":    employee.get("department", ""),
            "role":          employee.get("role", ""),
            "has_helmet":    status_data["has_helmet"],
            "has_vest":      status_data["has_vest"],
            "missing_ppe":   status_data["missing"],
            "status":        status_data["status"],
            "camera_id":     camera_id or "CAM-01",
            "timestamp":     time.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            response = requests.post(
                f"{self.backend_url}/api/report",
                json=payload,
                timeout=3
            )
            if response.status_code == 200:
                result = response.json()
                print(f"[Reporter] Backend saved → Log ID: {result.get('log_id')}")
            else:
                print(f"[Reporter] Backend error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print("[Reporter] Backend not reachable — check will still save to Excel")
        except Exception as e:
            print(f"[Reporter] Error: {e}")