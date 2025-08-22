"""ZIP file creation utilities"""
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def create_artifact_zip(artifacts: Dict[str, Any], output_path: Path) -> None:
    """
    Create ZIP file with all artifacts

    Args:
        artifacts: Generated artifacts dict
        output_path: Path to output ZIP file
    """
    # Create a temporary directory to store files before zipping
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Add summary
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "endpoints": artifacts.get("endpoint_count", 0),
            "cases_per_endpoint": artifacts.get("cases_per_endpoint", 0),
            "outputs": list(artifacts.keys()),
            "total_cases": artifacts.get("total_cases", 0)
        }
        
        summary_file = temp_path / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Add JUnit tests
        if "junit" in artifacts:
            junit_dir = temp_path / "artifacts" / "junit"
            junit_dir.mkdir(parents=True, exist_ok=True)
            for file_name, content in artifacts["junit"].items():
                file_path = junit_dir / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)

        # Add Python tests
        if "python" in artifacts:
            python_dir = temp_path / "artifacts" / "python"
            python_dir.mkdir(parents=True, exist_ok=True)
            for file_name, content in artifacts["python"].items():
                file_path = python_dir / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)

        # Add Node.js tests
        if "nodejs" in artifacts:
            nodejs_dir = temp_path / "artifacts" / "nodejs"
            nodejs_dir.mkdir(parents=True, exist_ok=True)
            for file_name, content in artifacts["nodejs"].items():
                file_path = nodejs_dir / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)

        # Add Postman collection
        if "postman" in artifacts:
            postman_dir = temp_path / "artifacts" / "postman"
            postman_dir.mkdir(parents=True, exist_ok=True)
            collection_file = postman_dir / "collection.json"
            with open(collection_file, 'w') as f:
                json.dump(artifacts["postman"], f, indent=2)

        # Add WireMock stubs
        if "wiremock" in artifacts:
            wiremock_dir = temp_path / "artifacts" / "wiremock" / "mappings"
            wiremock_dir.mkdir(parents=True, exist_ok=True)
            for idx, stub in enumerate(artifacts["wiremock"]):
                stub_file = wiremock_dir / f"stub_{idx:03d}.json"
                with open(stub_file, 'w') as f:
                    json.dump(stub, f, indent=2)

        # Add data files
        if "json" in artifacts:
            data_dir = temp_path / "artifacts" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            json_file = data_dir / "test_data.json"
            with open(json_file, 'w') as f:
                json.dump(artifacts["json"], f, indent=2)

        if "csv" in artifacts:
            data_dir = temp_path / "artifacts" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            csv_file = data_dir / "test_data.csv"
            with open(csv_file, 'w') as f:
                f.write(artifacts["csv"])

        if "sql" in artifacts:
            data_dir = temp_path / "artifacts" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            sql_file = data_dir / "test_data.sql"
            with open(sql_file, 'w') as f:
                f.write(artifacts["sql"])

        # Use Python zipfile module (primary method for containerized environments)
        import zipfile
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
                # Add all files to the ZIP
                for file_path in temp_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            arcname = file_path.relative_to(temp_path)
                            # Skip very deep nested files that might cause compatibility issues
                            if len(arcname.parts) <= 8:  # Allow deeper nesting for Java project structure
                                zipf.write(file_path, arcname)
                        except Exception as file_e:
                            logger.warning(f"Skipping problematic file {file_path}: {file_e}")
                            continue
                
            logger.info(f"Created artifact ZIP with Python zipfile at {output_path}")
        except Exception as e:
            logger.error(f"Python zipfile failed: {e}")
            # Fallback: create a simple ZIP with just the summary
            try:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zipf:
                    summary_file = temp_path / "summary.json"
                    if summary_file.exists():
                        zipf.write(summary_file, "summary.json")
                    logger.info(f"Created minimal artifact ZIP at {output_path}")
            except Exception as final_e:
                logger.error(f"Final fallback failed: {final_e}")
                # Ultimate fallback: create an empty ZIP file
                try:
                    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zipf:
                        # Add a simple text file explaining the issue
                        zipf.writestr("error.txt", "ZIP generation encountered issues. Please try again.")
                    logger.info(f"Created error ZIP at {output_path}")
                except Exception as ultimate_e:
                    logger.error(f"Ultimate fallback failed: {ultimate_e}")
                    # If all else fails, we must succeed - create a basic ZIP
                    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as zipf:
                        zipf.writestr("summary.json", json.dumps({"error": "ZIP generation failed", "generated_at": datetime.utcnow().isoformat()}, indent=2))
                    logger.info(f"Created basic error ZIP at {output_path}")
