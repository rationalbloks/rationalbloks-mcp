# ============================================================================
# RATIONALBLOKS MCP - FRONTEND CLIENT
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Client for frontend operations. Uses Backend client internally
# for operations that require API access (like create_backend).
# ============================================================================

import os
import subprocess
import shutil
from pathlib import Path
from typing import Any

from ..backend.client import LogicBlokClient

# Public API
__all__ = ["FrontendClient"]


# GitHub repository for the template
TEMPLATE_REPO = "https://github.com/rationalbloks/rationalbloksfront.git"
TEMPLATE_BRANCH = "main"


class FrontendClient:
    """Client for frontend generation operations.
    
    Provides:
    - Template cloning from GitHub
    - Template file exploration
    - Backend integration via LogicBlokClient
    - Frontend configuration
    """
    
    def __init__(self, api_key: str | None = None) -> None:
        """Initialize frontend client.
        
        Args:
            api_key: RationalBloks API key (required for create_backend)
        """
        self.api_key = api_key
        self._backend_client: LogicBlokClient | None = None
    
    async def close(self) -> None:
        """Close any open connections."""
        if self._backend_client:
            await self._backend_client.close()
    
    async def __aenter__(self) -> "FrontendClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    def _get_backend_client(self) -> LogicBlokClient:
        """Get or create backend client."""
        if not self.api_key:
            raise ValueError("API key required for backend operations")
        if not self._backend_client:
            self._backend_client = LogicBlokClient(self.api_key)
        return self._backend_client
    
    # ========================================================================
    # TEMPLATE OPERATIONS
    # ========================================================================
    
    async def clone_template(
        self,
        destination: str,
        project_name: str,
    ) -> dict[str, Any]:
        """Clone the rationalbloksfront template to a local directory.
        
        Args:
            destination: Directory to clone into
            project_name: Name for the cloned project
        
        Returns:
            Result with clone location and next steps
        """
        dest_path = Path(destination).expanduser().resolve()
        project_path = dest_path / project_name
        
        # Check if destination exists
        if project_path.exists():
            return {
                "success": False,
                "error": f"Directory already exists: {project_path}",
                "suggestion": "Choose a different project name or delete the existing directory",
            }
        
        # Ensure parent directory exists
        dest_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone the repository
            result = subprocess.run(
                [
                    "git", "clone",
                    "--depth", "1",
                    "--branch", TEMPLATE_BRANCH,
                    TEMPLATE_REPO,
                    str(project_path),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Git clone failed: {result.stderr}",
                    "suggestion": "Ensure git is installed and the repository is accessible",
                }
            
            # Remove .git directory to start fresh
            git_dir = project_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
            
            # Initialize new git repo
            subprocess.run(
                ["git", "init"],
                cwd=str(project_path),
                capture_output=True,
            )
            
            return {
                "success": True,
                "project_path": str(project_path),
                "template_version": TEMPLATE_BRANCH,
                "next_steps": [
                    f"cd {project_path}",
                    "npm install",
                    "npm run dev",
                ],
                "files_created": self._list_files(project_path),
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Git clone timed out after 120 seconds",
                "suggestion": "Check your network connection",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Git is not installed or not in PATH",
                "suggestion": "Install git: https://git-scm.com/downloads",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_template_structure(
        self,
        path: str = "",
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Get the file structure of the template.
        
        Args:
            path: Subdirectory to explore (empty for root)
            max_depth: Maximum directory depth to show
        
        Returns:
            Tree structure of the template
        """
        # This would ideally fetch from GitHub API
        # For now, return the known structure
        return {
            "template": "rationalbloksfront",
            "structure": {
                "src/": {
                    "components/": ["Header.tsx", "Footer.tsx", "..."],
                    "pages/": ["Home.tsx", "Dashboard.tsx", "..."],
                    "hooks/": ["useAuth.ts", "useApi.ts", "..."],
                    "services/": ["api.ts", "auth.ts", "..."],
                    "styles/": ["globals.css", "..."],
                    "App.tsx": "Main application component",
                    "main.tsx": "Entry point",
                },
                "public/": ["favicon.ico", "logo.svg"],
                "package.json": "Dependencies and scripts",
                "vite.config.ts": "Vite configuration",
                "tsconfig.json": "TypeScript configuration",
                ".env.example": "Environment template",
            },
            "key_files": [
                {"path": "src/services/api.ts", "purpose": "API client configuration"},
                {"path": ".env.example", "purpose": "Environment variables template"},
                {"path": "src/App.tsx", "purpose": "Main application routes"},
            ],
        }
    
    async def read_template_file(
        self,
        file_path: str,
    ) -> dict[str, Any]:
        """Read a specific file from the template.
        
        Args:
            file_path: Path to the file within the template
        
        Returns:
            File content and metadata
        """
        # This would fetch from GitHub raw content
        # For now, return a placeholder
        return {
            "path": file_path,
            "note": "Use clone_template to get full file access",
            "github_url": f"https://github.com/rationalbloks/rationalbloksfront/blob/main/{file_path}",
        }
    
    # ========================================================================
    # BACKEND INTEGRATION
    # ========================================================================
    
    async def create_backend(
        self,
        name: str,
        schema: dict,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a backend project via the Backend MCP.
        
        Args:
            name: Project name
            schema: JSON schema in FLAT format
            description: Optional project description
        
        Returns:
            Backend project details with API URLs
        """
        client = self._get_backend_client()
        result = await client.create_project(
            name=name,
            schema=schema,
            description=description,
        )
        return result
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    async def configure_api_url(
        self,
        project_path: str,
        api_url: str,
    ) -> dict[str, Any]:
        """Configure the API URL in the frontend project.
        
        Args:
            project_path: Path to the cloned frontend project
            api_url: Backend API URL (e.g., https://project-abc.customersblok.rationalbloks.com)
        
        Returns:
            Configuration result
        """
        project = Path(project_path).expanduser().resolve()
        
        if not project.exists():
            return {
                "success": False,
                "error": f"Project directory not found: {project}",
            }
        
        # Check for .env file
        env_file = project / ".env"
        env_example = project / ".env.example"
        
        # Create .env from example if needed
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
        
        # Update or create .env with API URL
        env_content = ""
        if env_file.exists():
            env_content = env_file.read_text()
        
        # Update VITE_API_URL
        lines = env_content.split("\n")
        updated = False
        new_lines = []
        
        for line in lines:
            if line.startswith("VITE_API_URL="):
                new_lines.append(f"VITE_API_URL={api_url}")
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            new_lines.append(f"VITE_API_URL={api_url}")
        
        env_file.write_text("\n".join(new_lines))
        
        return {
            "success": True,
            "env_file": str(env_file),
            "api_url": api_url,
            "next_steps": [
                "npm run dev  # Start development server",
                f"# Your frontend will connect to {api_url}",
            ],
        }
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _list_files(self, path: Path, prefix: str = "") -> list[str]:
        """List files in a directory recursively."""
        files = []
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    files.append(f"{prefix}{item.name}/")
                    if len(files) < 50:  # Limit depth
                        files.extend(self._list_files(item, f"{prefix}  "))
                else:
                    files.append(f"{prefix}{item.name}")
        except PermissionError:
            pass
        return files[:50]  # Limit total files shown
