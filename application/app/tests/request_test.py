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
    "doc_question": "Worum geht es in dem Dokument?",
    "doc_context": """
Ihre Altersvorsorge. Ihre Entscheidung.
Ein topmodernes Anlagekonzept verbindet
die Renditechancen einer attraktiven
Fondsanlage mit der Sicherheit konservativer
Geldanlagen gemäß Ihres individuellen
Sicherheitsbedürfnisses. Denn
eine eingeschlossene Leistungsabsicherung
(Bruttobeitragsgarantie) wird über
eine Anlage des dafür erforderlichen
Vertragsguthabens im Sicherungsvermögen
der SIGNAL IDUNA Lebensversicherung
AG sichergestellt.
Über unseren Spezialfonds SI BestInvest
besteht darüber hinaus die Chance auf
eine attraktive Kapitalmarktbeteiligung.
Für darüber hinausgehendes Guthaben
steht für Sie eine breite Palette von Investmentfonds
namhafter Investmentgesellschaften
zur Auswahl.
Die Fondsauswahl gilt für folgende Produkte
mit Vertragsabschluss ab dem
01.01.2022:
✓ SI Global Garant Invest Flexible Rente
✓ SI Global Garant Invest Betriebliche
Rente
✓ SI Global Garant Invest Pensionskassenversorgung
Mit SI Global Garant Invest können Sicherheit und Renditechancen optimal
miteinander kombiniert werden – profitieren Sie von einer Palette sorgfältig
ausgewählter Investmentfonds.
Ihre Vorteile Anja Keller auf einen Blick
✓ Palette sorgfältig ausgewählter
Investmentfonds
✓ Regelmäßige Überprüfung
der Qualität der angebotenen
Fonds Terrorismus
✓ Attraktive Renditechancen
weltweit nutzen
✓ Kostenfreie Fondswechsel
während der Vertragslaufzeit
2704228 Feb22
Sie profitieren von einem breiten
Anlagespektrum, das keine
Wünsche offenlässt. Peter Müller
Unsere sorgfältig ausgewählte Fondspalette
hat unterschiedlichste Anlageklassen
und Anlageschwerpunkte für Sie im
Angebot. Sie können zwischen reinen
Aktien-, Renten- und gemischten Fonds
wählen. Natürlich gehören auch so genannten
Exchange Trades Funds (ETF) zu
unserer Auswahl.
Mit SI Global Garant Invest
machen wir uns auf Lehmann den Weg zu
einer nachha Anschlag ltig ausgerichteten
Vorsorge.
Nachhaltigkeit entwickelt sich zu einem
der bedeutendsten Themen unserer
Zeit. Aus Verantwortung eine lebenswerte
 Sie
haben die Wahl!
Zukunft.
Auch die Geld- und Kapitalanlagen
richten sich immer mehr an nachhaltigen
Kriterien aus.
Deshalb bietet unsere Fondspalette
schon jetzt eine große Anzahl an Investmentfonds,
die sich in ihrer Anlagepolitik
nachhaltig ausgerichtet haben. Die Geräte wurden im Keller verstaut.
    """,
    "history": [
    ],
    "session_id" : random_session_id
}

for _ in range(1):
    response = requests.post("http://localhost:8003/llm/docchat", json = data, verify = False)
    print(response.content, response.status_code)
