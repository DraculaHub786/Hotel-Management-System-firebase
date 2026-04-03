import os

# Ensure protobuf never tries the C extension under Python 3.14 on Render.
# Python auto-imports sitecustomize during startup if this file is on sys.path.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
