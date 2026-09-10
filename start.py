import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dist = os.path.join(base_dir, "frontend", "dist")

    # If dist doesn't exist, build it
    if not os.path.isdir(frontend_dist) or not os.path.isfile(os.path.join(frontend_dist, "index.html")):
        print("Frontend build not found. Running 'npm run build'...")
        subprocess.run(["npm", "run", "build"], cwd=os.path.join(base_dir, "frontend"), check=True, shell=True)

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting SANJAL AI-Powered Block Planner on http://{host}:{port}...")
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, reload=False, app_dir=os.path.join(base_dir, "backend"))

if __name__ == "__main__":
    main()
