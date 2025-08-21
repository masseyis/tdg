"""ZIP file creation utilities"""
import json
import logging
import zipfile
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
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add summary
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "endpoints": artifacts.get("endpoint_count", 0),
            "cases_per_endpoint": artifacts.get("cases_per_endpoint", 0),
            "outputs": list(artifacts.keys()),
            "total_cases": artifacts.get("total_cases", 0)
        }
        zipf.writestr("summary.json", json.dumps(summary, indent=2))
        
        # Add JUnit tests
        if "junit" in artifacts:
            for file_name, content in artifacts["junit"].items():
                zipf.writestr(f"artifacts/junit/{file_name}", content)
        
        # Add Postman collection
        if "postman" in artifacts:
            zipf.writestr(
                "artifacts/postman/collection.json",
                json.dumps(artifacts["postman"], indent=2)
            )
        
        # Add WireMock stubs
        if "wiremock" in artifacts:
            for idx, stub in enumerate(artifacts["wiremock"]):
                zipf.writestr(
                    f"artifacts/wiremock/mappings/stub_{idx:03d}.json",
                    json.dumps(stub, indent=2)
                )
        
        # Add data files
        if "json" in artifacts:
            zipf.writestr(
                "artifacts/data/test_data.json",
                json.dumps(artifacts["json"], indent=2)
            )
        
        if "csv" in artifacts:
            zipf.writestr(
                "artifacts/data/test_data.csv",
                artifacts["csv"]
            )
        
        if "sql" in artifacts:
            zipf.writestr(
                "artifacts/data/test_data.sql",
                artifacts["sql"]
            )
    
    logger.info(f"Created artifact ZIP at {output_path}")