import sys
from pathlib import Path

# Add server/ml-service to path so "app" can be imported
root_dir = Path(__file__).parent.parent
ml_service_dir = root_dir / "faceattend" / "server" / "ml-service"
sys.path.insert(0, str(ml_service_dir))
sys.path.insert(0, str(root_dir))
