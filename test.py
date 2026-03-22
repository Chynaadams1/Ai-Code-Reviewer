def hello():
    print("testing AI review")
```

---

**Step 2 — Save it on a new branch:**
1. Scroll down to the bottom of the page
2. Select **"Create a new branch"** (don't commit to main)
3. Name the branch `test-review`
4. Click **"Propose new file"**

---

**Step 3 — Open the Pull Request:**
1. GitHub will automatically show a **"Compare & pull request"** button
2. Click it
3. Click **"Create pull request"**

---

**Then watch your uvicorn terminal** — you should see:
```
INFO: POST /webhook/github HTTP/1.1" 200 OK
