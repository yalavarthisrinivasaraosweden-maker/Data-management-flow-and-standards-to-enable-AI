"""
Unified API server that registers all modules.
"""

from restful_api import app

# Register extension routes on the shared FastAPI app.

import version_control_api  # noqa: F401
import data_quality_api  # noqa: F401
import data_analysis_api  # noqa: F401
import ml_api  # noqa: F401
import security_privacy  # noqa: F401
import backup_recovery  # noqa: F401
import collaboration_sharing  # noqa: F401


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
