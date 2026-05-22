import time
import requests

BASE_URL = "http://127.0.0.1:5000"

session = requests.Session()

def test_route(name, url, method='GET', data=None):
    start = time.time()
    if method == 'POST':
        r = session.post(BASE_URL + url, data=data, allow_redirects=True)
    else:
        r = session.get(BASE_URL + url, allow_redirects=True)
    end = time.time()
    elapsed = round((end - start) * 1000, 2)
    status = "✅ PASS" if r.status_code in [200, 302] else "❌ FAIL"
    print(f"{status} | {name:<35} | {elapsed} ms | Status: {r.status_code}")
    return elapsed

print("\n" + "="*75)
print("PERFORMANCE TEST — Full-Stack Inventory Management System")
print("="*75)

# Login first
times = []
times.append(test_route("Login (POST)", "/login", "POST",
    {"username": "admin", "password": "Admin@1234"}))

# Test all routes
routes = [
    ("Dashboard", "/dashboard"),
    ("Products Page", "/products"),
    ("Suppliers Page", "/suppliers"),
    ("Transactions Page", "/transactions"),
    ("AI Predictions Page", "/predict"),
    ("Reports Page", "/reports"),
    ("Change Password Page", "/change_password"),
    ("Export CSV", "/export_csv"),
    ("Export PDF", "/export_pdf"),
]

for name, url in routes:
    times.append(test_route(name, url))

print("="*75)
print(f"Total Routes Tested : {len(times)}")
print(f"Average Response Time: {round(sum(times)/len(times), 2)} ms")
print(f"Fastest Route       : {min(times)} ms")
print(f"Slowest Route       : {max(times)} ms")
print(f"All under 2 seconds : {'✅ YES' if max(times) < 2000 else '❌ NO'}")
print("="*75 + "\n")