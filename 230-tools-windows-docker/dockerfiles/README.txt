All three files here are UNTESTED: written 2026-10-18 after the preflight showed the
Windows Docker daemon is not running on this machine
(`docker.exe run --rm hello-world` failed: "open //./pipe/docker_engine: The system
cannot find the file specified" - Docker Desktop not started).

What was tested on the host instead (WSL2, not a Windows-without-WSL proof):
- the local commands the Dockerfiles wrap: pip installs, sparkMeasure with the Maven
  jar, DataFlint plugin attached to a driver UI (logs/dataflint.out), and a pip-pyspark
  History Server reading the same event-log directory the compose file shares
  (logs/hs_stage17.json).
- image tag existence: apache/spark:3.5.9-scala2.12-java17-python3-ubuntu and 4.2.0*
  verified via hub.docker.com API on 2026-10-18.

A Linux/WSL run or a written Dockerfile does not verify Windows-without-WSL operation.
Required backend assumptions for the bank: Docker Desktop (Windows containers off,
Linux containers on, WSL2 backend OR Hyper-V backend - both serve Linux containers to
PowerShell without the user touching WSL), an internal Docker Hub mirror if Docker Hub
is blocked, and either Maven Central access or pre-downloaded jars (see the URLs in
Dockerfile.analysers).
