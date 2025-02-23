import requests
import google.oauth2.id_token
import google.auth.transport.requests
import random
import string


def randomword(length: int) -> str:
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


# Get GCP SA Token for authorization with IAM
auth_req = google.auth.transport.requests.Request()
# token = google.oauth2.id_token.fetch_id_token(auth_req, "https://chat-backend-test-z7fmzpkxjq-ey.a.run.app")
# token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFkZjVlNzEwZWRmZWJlY2JlZmE5YTYxNDk1NjU0ZDAzYzBiOGVkZjgiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIzMjU1NTk0MDU1OS5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsImF1ZCI6IjMyNTU1OTQwNTU5LmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTE1OTMwNDE3NDM0NDEzNTEyNzQyIiwiaGQiOiJzaWduYWwtaWR1bmEuZGUiLCJlbWFpbCI6InUxNjI0NzVhQHNpZ25hbC1pZHVuYS5kZSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdF9oYXNoIjoiU2xEdzZlbWRqV2ZkVktSZ2phY3NYZyIsImlhdCI6MTcxMTU0ODU3OSwiZXhwIjoxNzExNTUyMTc5fQ.oNfrnDHz9ltC1glStsMR5x4HFLPolkK5b6EjmtetK20DU_WGwo03aU8wr25wU0NbMVxG2344iRbK_rMgo5IUxc8CVG-t_TyVV_owyRsve6AahYSNHPu1joH5hkUw63gBs1mRD_zG-AOW-8eWBATuzUjThdzxl94-tXMUVl5Ujg6-NZQQgBjnSxmjh4GflbCAz-UyeJdfirvLXSk6weSkmQ5sU8J7d6UGyUXCpTCre49UUu3rwAvDAZmDpVGrHliR9dZUbLpCTzTVBXbxlwf0HP53VjsRffd8TtywzJGF9eq945H5g1B2AXNKjMCFrTOubaf_Eny9zu5q4HdGO3tphg"
# Add an authorization header for the request to backend
# HEADERS = {
#     "Authorization": "Bearer " + token
# }

random_session_id:str = randomword(10)

data = {
    "question": "Wer ist Thomas Mueller?",
    "history": [
    ],
    "session_id" : random_session_id,
    "oid_hashed": "oid"
}

for _ in range(1):
    response = requests.post("http://localhost:8003/llm/textchat", json = data, verify = True)
    print(response.content, response.status_code)
