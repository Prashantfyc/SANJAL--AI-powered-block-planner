import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")
    frontend_dist = os.path.join(frontend_dir, "dist")

    # Add backend directory to sys.path so app and seed modules resolve
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Ensure frontend build exists
    index_html = os.path.join(frontend_dist, "index.html")
    if not os.path.isfile(index_html):
        print("Frontend dist not found. Attempting 'npm run build'...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
        except Exception as e:
            print(f"Notice: Frontend build step failed ({e}). Proceeding with available files.")

    # Seed initial data if DB is empty
    try:
        from seed import seed_data
        seed_data()
    except Exception as e:
        print(f"Seed note: {e}")

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting SANJAL AI-Powered Block Planner on http://{host}:{port}...")
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, reload=False, app_dir=backend_dir)

if __name__ == "__main__":
    main()
