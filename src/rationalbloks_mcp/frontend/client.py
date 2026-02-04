# ============================================================================
# RATIONALBLOKS MCP - FRONTEND CLIENT (THIN LAYER)
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Client for frontend bootstrap operations ONLY.
# The AI agent writes all views, forms, and custom UI.
#
# METHODS:
#   - clone_template: Clone rationalbloksfront from GitHub
#   - generate_types: Generate TypeScript interfaces from schema
#   - generate_api_service: Generate datablokApi.ts (THE ONE WAY glue)
#   - configure_api_url: Set VITE_DATABASE_API_URL in .env
#   - get_template_structure: Explore template file structure
#
# ============================================================================

import re
import subprocess
import shutil
from pathlib import Path
from typing import Any

# Public API
__all__ = ["FrontendClient"]

# GitHub template repository
TEMPLATE_REPO = "https://github.com/velosovictor/rationalbloksfront.git"
TEMPLATE_BRANCH = "main"


class FrontendClient:
    """Client for frontend bootstrap operations.
    
    This is a THIN LAYER that only provides:
    - Template cloning
    - Type generation from schema
    - API service generation (datablokApi.ts)
    - Environment configuration
    
    The AI agent writes all views, forms, and custom UI.
    """
    
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
    
    async def close(self) -> None:
        pass
    
    async def __aenter__(self) -> "FrontendClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        return "".join(word.capitalize() for word in re.split(r"[_\s-]", name))
    
    def _schema_type_to_ts(self, schema_type: str) -> str:
        """Convert schema type to TypeScript type."""
        mapping = {
            "string": "string",
            "text": "string",
            "integer": "number",
            "decimal": "number",
            "boolean": "boolean",
            "uuid": "string",
            "date": "string",
            "datetime": "string",
            "json": "Record<string, unknown>",
        }
        return mapping.get(schema_type, "unknown")
    
    def _get_singular(self, type_name: str) -> str:
        """Get singular form of type name."""
        if type_name.endswith("ies"):
            return type_name[:-3] + "y"
        elif type_name.endswith("s") and len(type_name) > 1:
            return type_name[:-1]
        return type_name
    
    # ========================================================================
    # BOOTSTRAP METHODS
    # ========================================================================
    
    async def clone_template(
        self,
        destination: str,
        project_name: str,
    ) -> dict[str, Any]:
        """Clone the rationalbloksfront template from GitHub.
        
        Creates a fresh project with:
        - React + Vite + TypeScript
        - frontblok-auth and frontblok-crud installed
        - MUI components
        - Template views and shared components
        """
        dest = Path(destination).resolve()
        project_dir = dest / project_name
        
        if project_dir.exists():
            return {
                "success": False, 
                "error": f"Directory already exists: {project_dir}"
            }
        
        dest.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone the template
            subprocess.run(
                ["git", "clone", "--branch", TEMPLATE_BRANCH, TEMPLATE_REPO, project_name],
                cwd=str(dest),
                check=True,
                capture_output=True,
            )
            
            # Remove .git directory
            git_dir = project_dir / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
            
            # Initialize new git repo
            subprocess.run(
                ["git", "init"],
                cwd=str(project_dir),
                check=True,
                capture_output=True,
            )
            
            return {
                "success": True,
                "project_path": str(project_dir),
                "next_steps": [
                    "1. Use generate_types with your schema",
                    "2. Use generate_api_service with your schema",
                    "3. Use configure_api_url with your backend URL",
                    "4. Write custom views for each entity (AI creativity!)",
                    "5. Run npm install && npm run dev",
                ],
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git clone failed: {e.stderr.decode() if e.stderr else str(e)}",
            }
    
    async def generate_types(
        self,
        project_path: str,
        schema: dict,
    ) -> dict[str, Any]:
        """Generate TypeScript interfaces from schema.
        
        Creates src/types/generated.ts with interfaces for each entity.
        """
        project = Path(project_path).resolve()
        
        if not project.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        
        types_content = '''// ============================================================================
// AUTO-GENERATED TYPES - Do not edit manually
// Generated by RationalBloks Frontend MCP
// ============================================================================

'''
        for table_name, fields in schema.items():
            type_name = self._pascal_case(table_name)
            singular = self._get_singular(type_name)
            
            # Collect enum types for this entity
            enum_types = {}
            for field_name, field_def in fields.items():
                if "enum" in field_def:
                    enum_types[field_name] = field_def["enum"]
            
            # Main interface
            types_content += f"export interface {singular} {{\n"
            types_content += "  id: string;\n"
            
            for field_name, field_def in fields.items():
                if field_name.startswith("_"):
                    continue
                
                # Handle enum types
                if "enum" in field_def:
                    enum_values = " | ".join([f"'{v}'" for v in field_def["enum"]])
                    ts_type = enum_values
                else:
                    ts_type = self._schema_type_to_ts(field_def.get("type", "string"))
                
                optional = "" if field_def.get("required") else "?"
                types_content += f"  {field_name}{optional}: {ts_type};\n"
            
            types_content += "  created_at: string;\n"
            types_content += "  updated_at: string;\n"
            types_content += "}\n\n"
            
            # Create input type
            types_content += f"export interface Create{singular}Input {{\n"
            for field_name, field_def in fields.items():
                if field_name.startswith("_") or field_name == "user_id":
                    continue
                
                if "enum" in field_def:
                    enum_values = " | ".join([f"'{v}'" for v in field_def["enum"]])
                    ts_type = enum_values
                else:
                    ts_type = self._schema_type_to_ts(field_def.get("type", "string"))
                
                optional = "" if field_def.get("required") else "?"
                types_content += f"  {field_name}{optional}: {ts_type};\n"
            types_content += "}\n\n"
            
            # Update input type
            types_content += f"export type Update{singular}Input = Partial<Create{singular}Input>;\n\n"
        
        types_file = project / "src" / "types" / "generated.ts"
        types_file.parent.mkdir(parents=True, exist_ok=True)
        types_file.write_text(types_content, encoding="utf-8")
        
        return {
            "success": True,
            "file": str(types_file),
            "entities": list(schema.keys()),
        }
    
    async def generate_api_service(
        self,
        project_path: str,
        schema: dict,
        api_url: str | None = None,
    ) -> dict[str, Any]:
        """Generate datablokApi.ts - THE ONE WAY glue file.
        
        Creates src/services/datablokApi.ts with:
        - authApi singleton from frontblok-auth
        - CRUD via getApi() from frontblok-crud
        - ClientAuthProvider and useClientAuth for React context
        - ENTITIES constant for type-safe entity names
        """
        project = Path(project_path).resolve()
        
        if not project.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        
        default_url = api_url or 'http://localhost:8000'
        
        # Build ENTITIES constant
        entities_lines = []
        for table_name in schema.keys():
            const_name = table_name.upper()
            entities_lines.append(f"  {const_name}: '{table_name}'")
        entities_const = ",\n".join(entities_lines)
        
        api_content = f'''// ============================================================================
// DATABLOK API SERVICE - THE ONE WAY Architecture
// Generated by RationalBloks Frontend MCP
// ============================================================================
//
// ARCHITECTURE:
// ┌─────────────────────────────────────────────────────────────────────────┐
// │  frontblok-auth.createAuthApi()   →  Auth singleton (login, tokens)     │
// │  frontblok-crud.initApi()         →  CRUD via getApi()                  │
// │  This file                        →  ENTITIES constant + re-exports     │
// └─────────────────────────────────────────────────────────────────────────┘
//
// USAGE IN COMPONENTS:
//   import {{ getApi, ENTITIES }} from '../services/datablokApi';
//   const items = await getApi().getAll<MyType>(ENTITIES.MY_TABLE);
//
// ============================================================================

import {{ createAuthApi, createAuthProvider, useAuth, getStoredUser, getStoredToken, isAuthenticated }} from '@rationalbloks/frontblok-auth';
import {{ initApi, getApi }} from '@rationalbloks/frontblok-crud';
import type {{ User }} from '@rationalbloks/frontblok-auth';

// ============================================================================
// RE-EXPORTS
// ============================================================================
export {{ getStoredUser, getStoredToken, isAuthenticated }};
export type {{ User }};
export {{ getApi }};

// ============================================================================
// AUTH API SINGLETON
// ============================================================================
const DATABLOK_API = import.meta.env.VITE_DATABASE_API_URL || '{default_url}';

export const authApi = createAuthApi(DATABLOK_API);

// Initialize frontblok-crud with authApi
// THE ONE WAY: frontblok-crud uses frontblok-auth's HTTP layer
initApi(authApi);

// ============================================================================
// ENTITY NAMES
// ============================================================================
export const ENTITIES = {{
{entities_const}
}} as const;

export type EntityName = typeof ENTITIES[keyof typeof ENTITIES];

// ============================================================================
// AUTH CONTEXT
// ============================================================================
export const ClientAuthProvider = createAuthProvider(authApi);
export const useClientAuth = useAuth;
'''
        
        api_file = project / "src" / "services" / "datablokApi.ts"
        api_file.parent.mkdir(parents=True, exist_ok=True)
        api_file.write_text(api_content, encoding="utf-8")
        
        return {
            "success": True,
            "file": str(api_file),
            "entities": list(schema.keys()),
            "architecture": "THE_ONE_WAY",
        }
    
    async def configure_api_url(
        self,
        project_path: str,
        api_url: str,
    ) -> dict[str, Any]:
        """Set the backend API URL in .env file."""
        project = Path(project_path).resolve()
        
        if not project.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        
        env_file = project / ".env"
        env_example = project / ".env.example"
        
        # If .env doesn't exist, copy from .env.example
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
        
        if not env_file.exists():
            # Create minimal .env
            env_content = f"VITE_DATABASE_API_URL={api_url}\n"
            env_file.write_text(env_content, encoding="utf-8")
        else:
            # Update existing .env
            content = env_file.read_text(encoding="utf-8")
            
            if "VITE_DATABASE_API_URL=" in content:
                # Replace existing line
                lines = content.split("\n")
                new_lines = []
                for line in lines:
                    if line.startswith("VITE_DATABASE_API_URL="):
                        new_lines.append(f"VITE_DATABASE_API_URL={api_url}")
                    else:
                        new_lines.append(line)
                content = "\n".join(new_lines)
            else:
                # Add new line
                content += f"\nVITE_DATABASE_API_URL={api_url}\n"
            
            env_file.write_text(content, encoding="utf-8")
        
        return {
            "success": True,
            "file": str(env_file),
            "api_url": api_url,
        }
    
    async def get_template_structure(
        self,
        path: str = "",
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Get the structure of the rationalbloksfront template.
        
        Returns a tree view of key directories and files.
        """
        # Return a static representation of the template structure
        structure = """
rationalbloksfront/
├── src/
│   ├── App.tsx                    ← Provider hierarchy + routes
│   ├── main.tsx                   ← createAppRoot(App, config)
│   ├── components/
│   │   ├── shared/                ← Reusable UI components
│   │   │   ├── Navbar.tsx         ← createNavbar factory
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── ...
│   │   └── views/                 ← Page components (YOU write these)
│   │       ├── ClientAuthView.tsx
│   │       ├── UserSettingsView.tsx
│   │       ├── ForgotPasswordView.tsx
│   │       └── ...                ← Add your custom views here
│   ├── config/
│   │   └── Navbar.tsx             ← createNavbar() with your nav items
│   ├── services/
│   │   ├── datablokApi.ts         ← THE ONE WAY glue (generated)
│   │   └── logicblokApi.ts        ← Business logic API (optional)
│   ├── types/
│   │   └── generated.ts           ← TypeScript types (generated)
│   ├── theme/
│   │   └── index.ts               ← createAppTheme()
│   └── styles/
│       └── globals.css            ← Global styles
├── .env                           ← VITE_DATABASE_API_URL
├── package.json                   ← Dependencies
├── vite.config.ts                 ← Vite configuration
└── tsconfig.json                  ← TypeScript configuration

KEY PATTERNS:
- All CRUD via getApi() from datablokApi
- All auth via useClientAuth() from datablokApi
- Views in src/components/views/
- Routes in App.tsx
- Navbar config in src/config/Navbar.tsx
"""
        
        return {
            "structure": structure.strip(),
            "key_files": [
                "src/App.tsx - Provider hierarchy and routes",
                "src/main.tsx - App bootstrap with createAppRoot",
                "src/services/datablokApi.ts - THE ONE WAY glue",
                "src/types/generated.ts - TypeScript interfaces",
                "src/config/Navbar.tsx - Navigation configuration",
                "src/components/views/ - Your custom view components",
            ],
        }
