# ============================================================================
# RATIONALBLOKS MCP - APP GENERATOR
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Complete app generation from template + schema.
# This is the core logic for the create_app tool.
#
# WORKFLOW:
# 1. Clone template
# 2. Create backend (schema → API)
# 3. Wait for deployment
# 4. Generate TypeScript types
# 5. Generate views for each entity
# 6. Update routes
# 7. Update navbar
# 8. Cleanup template files
# 9. Update package.json
# 10. Run npm install
# ============================================================================

import asyncio
import json
import re
import subprocess
import shutil
from pathlib import Path
from typing import Any
from datetime import datetime

# Public API
__all__ = ["AppGenerator"]


class AppGenerator:
    """
    Complete app generator that transforms a template into a working application.
    
    Usage:
        generator = AppGenerator(api_key="rb_sk_...")
        result = await generator.create_app(
            name="TaskManager",
            description="A task management app with projects and tasks",
            destination="~/projects",
            schema={...}  # Optional - will be inferred from description
        )
    """
    
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._backend_client = None
    
    async def create_app(
        self,
        name: str,
        description: str,
        destination: str,
        schema: dict | None = None,
        template: str = "rationalbloksfront",
        wait_for_deployment: bool = True,
        run_npm_install: bool = True,
    ) -> dict[str, Any]:
        """
        Create a complete application from template.
        
        Args:
            name: Application name (e.g., "TaskManager")
            description: What the app does (used for schema inference if no schema provided)
            destination: Parent directory to create project in
            schema: Optional backend schema (if not provided, must be inferred by AI first)
            template: Template to use (default: rationalbloksfront)
            wait_for_deployment: Wait for backend to deploy (default: True)
            run_npm_install: Run npm install after generation (default: True)
        
        Returns:
            Complete result with project path, backend URL, generated files, etc.
        """
        from ..backend.client import LogicBlokClient
        
        result = {
            "success": False,
            "app_name": name,
            "steps_completed": [],
            "steps_failed": [],
            "project_path": None,
            "backend": None,
            "generated_files": [],
            "next_steps": [],
        }
        
        # Validate inputs
        if not schema:
            return {
                **result,
                "error": "Schema is required. The AI agent should infer the schema from the description first using the create-project-from-description prompt.",
                "suggestion": "Provide a schema in FLAT format: {table: {field: {type: 'string', ...}}}",
            }
        
        dest_path = Path(destination).expanduser().resolve()
        project_slug = self._slugify(name)
        project_path = dest_path / project_slug
        
        # Step 1: Clone template
        try:
            clone_result = await self._clone_template(dest_path, project_slug)
            if not clone_result["success"]:
                result["steps_failed"].append({"step": "clone_template", "error": clone_result.get("error")})
                return {**result, "error": f"Clone failed: {clone_result.get('error')}"}
            result["steps_completed"].append("clone_template")
            result["project_path"] = str(project_path)
        except Exception as e:
            result["steps_failed"].append({"step": "clone_template", "error": str(e)})
            return {**result, "error": f"Clone failed: {e}"}
        
        # Step 2: Create backend
        try:
            async with LogicBlokClient(self.api_key) as client:
                backend_result = await client.create_project(
                    name=name,
                    schema=schema,
                    description=description,
                )
                result["backend"] = {
                    "project_id": backend_result.get("project_id"),
                    "project_code": backend_result.get("project_code"),
                    "job_id": backend_result.get("job_id"),
                }
                result["steps_completed"].append("create_backend")
                
                # Step 3: Wait for deployment
                if wait_for_deployment:
                    job_id = backend_result.get("job_id")
                    if job_id:
                        deployment_result = await self._wait_for_deployment(client, job_id)
                        if deployment_result["success"]:
                            result["steps_completed"].append("wait_for_deployment")
                            result["backend"]["status"] = "deployed"
                        else:
                            result["steps_failed"].append({
                                "step": "wait_for_deployment",
                                "error": deployment_result.get("error"),
                            })
                            # Continue anyway - deployment might still complete
                
                # Get project info for staging URL
                project_info = await client.get_project_info(backend_result["project_id"])
                staging_url = project_info.get("staging_url") or f"https://{backend_result['project_code']}-staging.customersblok.rationalbloks.com"
                result["backend"]["staging_url"] = staging_url
                
        except Exception as e:
            result["steps_failed"].append({"step": "create_backend", "error": str(e)})
            # Continue with frontend generation even if backend fails
        
        # Step 4: Generate TypeScript types
        try:
            types_file = self._generate_types(project_path, schema)
            result["generated_files"].append(str(types_file))
            result["steps_completed"].append("generate_types")
        except Exception as e:
            result["steps_failed"].append({"step": "generate_types", "error": str(e)})
        
        # Step 5: Generate API service
        try:
            api_file = self._generate_api_service(project_path, schema, staging_url if "staging_url" in locals() else None)
            result["generated_files"].append(str(api_file))
            result["steps_completed"].append("generate_api_service")
        except Exception as e:
            result["steps_failed"].append({"step": "generate_api_service", "error": str(e)})
        
        # Step 6: Generate views for each entity
        try:
            for table_name in schema.keys():
                view_files = self._generate_entity_views(project_path, table_name, schema[table_name])
                result["generated_files"].extend([str(f) for f in view_files])
            result["steps_completed"].append("generate_views")
        except Exception as e:
            result["steps_failed"].append({"step": "generate_views", "error": str(e)})
        
        # Step 7: Generate dashboard
        try:
            dashboard_file = self._generate_dashboard(project_path, name, schema)
            result["generated_files"].append(str(dashboard_file))
            result["steps_completed"].append("generate_dashboard")
        except Exception as e:
            result["steps_failed"].append({"step": "generate_dashboard", "error": str(e)})
        
        # Step 8: Update App.tsx with routes
        try:
            self._update_routes(project_path, schema)
            result["steps_completed"].append("update_routes")
        except Exception as e:
            result["steps_failed"].append({"step": "update_routes", "error": str(e)})
        
        # Step 9: Update Navbar
        try:
            self._update_navbar(project_path, name, schema)
            result["steps_completed"].append("update_navbar")
        except Exception as e:
            result["steps_failed"].append({"step": "update_navbar", "error": str(e)})
        
        # Step 10: Cleanup template-specific files
        try:
            self._cleanup_template_files(project_path)
            result["steps_completed"].append("cleanup_template")
        except Exception as e:
            result["steps_failed"].append({"step": "cleanup_template", "error": str(e)})
        
        # Step 11: Update package.json
        try:
            self._update_package_json(project_path, name, description)
            result["steps_completed"].append("update_package_json")
        except Exception as e:
            result["steps_failed"].append({"step": "update_package_json", "error": str(e)})
        
        # Step 12: Configure .env
        try:
            if "staging_url" in locals():
                self._configure_env(project_path, staging_url)
                result["steps_completed"].append("configure_env")
        except Exception as e:
            result["steps_failed"].append({"step": "configure_env", "error": str(e)})
        
        # Step 13: Run npm install
        if run_npm_install:
            try:
                npm_result = self._run_npm_install(project_path)
                if npm_result["success"]:
                    result["steps_completed"].append("npm_install")
                else:
                    result["steps_failed"].append({"step": "npm_install", "error": npm_result.get("error")})
            except Exception as e:
                result["steps_failed"].append({"step": "npm_install", "error": str(e)})
        
        # Determine overall success
        critical_steps = ["clone_template", "generate_types", "generate_views", "update_routes"]
        critical_completed = all(step in result["steps_completed"] for step in critical_steps)
        
        result["success"] = critical_completed
        result["next_steps"] = [
            f"cd {project_path}",
            "npm run dev" if "npm_install" in result["steps_completed"] else "npm install && npm run dev",
            f"Open http://localhost:5173",
        ]
        
        if result["backend"] and result["backend"].get("staging_url"):
            result["next_steps"].insert(0, f"Backend API: {result['backend']['staging_url']}")
        
        return result
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _slugify(self, name: str) -> str:
        """Convert name to URL-safe slug."""
        slug = name.lower().replace(" ", "-")
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        return slug
    
    def _pascal_case(self, name: str) -> str:
        """Convert to PascalCase."""
        return "".join(word.capitalize() for word in re.split(r"[_\s-]", name))
    
    def _camel_case(self, name: str) -> str:
        """Convert to camelCase."""
        pascal = self._pascal_case(name)
        return pascal[0].lower() + pascal[1:] if pascal else ""
    
    async def _clone_template(self, dest_path: Path, project_slug: str) -> dict:
        """Clone the template repository."""
        from .client import TEMPLATE_REPO, TEMPLATE_BRANCH
        
        project_path = dest_path / project_slug
        
        if project_path.exists():
            return {"success": False, "error": f"Directory already exists: {project_path}"}
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", TEMPLATE_BRANCH, TEMPLATE_REPO, str(project_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}
        
        # Remove .git and reinitialize
        git_dir = project_path / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        
        subprocess.run(["git", "init"], cwd=str(project_path), capture_output=True)
        
        return {"success": True, "project_path": str(project_path)}
    
    async def _wait_for_deployment(self, client, job_id: str, timeout: int = 300) -> dict:
        """Wait for backend deployment to complete."""
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                status = await client.get_job_status(job_id)
                if status.get("status") == "completed":
                    return {"success": True}
                if status.get("status") == "failed":
                    return {"success": False, "error": status.get("error", "Deployment failed")}
            except Exception:
                pass
            await asyncio.sleep(5)
        
        return {"success": False, "error": "Deployment timed out"}
    
    def _generate_types(self, project_path: Path, schema: dict) -> Path:
        """Generate TypeScript types from schema."""
        types_content = '''// ============================================================================
// AUTO-GENERATED TYPES - Do not edit manually
// Generated by RationalBloks Frontend MCP
// ============================================================================

'''
        for table_name, fields in schema.items():
            type_name = self._pascal_case(table_name)
            # Remove trailing 's' for singular type name if present
            if type_name.endswith("s") and len(type_name) > 1:
                type_name = type_name[:-1]
            
            types_content += f"export interface {type_name} {{\n"
            types_content += "  id: string;\n"
            
            for field_name, field_def in fields.items():
                ts_type = self._schema_type_to_ts(field_def.get("type", "string"))
                optional = "" if field_def.get("required") else "?"
                types_content += f"  {field_name}{optional}: {ts_type};\n"
            
            types_content += "  created_at: string;\n"
            types_content += "  updated_at: string;\n"
            types_content += "}\n\n"
            
            # Generate input types
            types_content += f"export interface Create{type_name}Input {{\n"
            for field_name, field_def in fields.items():
                if field_name == "user_id":  # Skip auto-set fields
                    continue
                ts_type = self._schema_type_to_ts(field_def.get("type", "string"))
                optional = "" if field_def.get("required") else "?"
                types_content += f"  {field_name}{optional}: {ts_type};\n"
            types_content += "}\n\n"
            
            types_content += f"export type Update{type_name}Input = Partial<Create{type_name}Input>;\n\n"
        
        types_file = project_path / "src" / "types" / "generated.ts"
        types_file.parent.mkdir(parents=True, exist_ok=True)
        types_file.write_text(types_content)
        
        return types_file
    
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
    
    def _generate_api_service(self, project_path: Path, schema: dict, api_url: str | None) -> Path:
        """Generate API service with CRUD operations for each entity."""
        api_content = '''// ============================================================================
// AUTO-GENERATED API SERVICE - Do not edit manually
// Generated by RationalBloks Frontend MCP
// ============================================================================

import { BaseApi } from "@rationalbloks/universalfront";

'''
        # Import types
        for table_name in schema.keys():
            type_name = self._pascal_case(table_name)
            if type_name.endswith("s") and len(type_name) > 1:
                type_name = type_name[:-1]
            api_content += f"import type {{ {type_name}, Create{type_name}Input, Update{type_name}Input }} from '../types/generated';\n"
        
        api_content += f'''
const API_URL = import.meta.env.VITE_DATABASE_API_URL || "{api_url or 'http://localhost:8000'}";

class AppApi extends BaseApi {{
  constructor() {{
    super(API_URL);
  }}

'''
        # Generate CRUD methods for each entity
        for table_name in schema.keys():
            type_name = self._pascal_case(table_name)
            singular = type_name[:-1] if type_name.endswith("s") and len(type_name) > 1 else type_name
            camel_plural = self._camel_case(table_name)
            camel_singular = camel_plural[:-1] if camel_plural.endswith("s") else camel_plural
            
            api_content += f'''  // {type_name} CRUD
  async get{type_name}(): Promise<{singular}[]> {{
    return this.get<{singular}[]>("/{table_name}");
  }}

  async get{singular}(id: string): Promise<{singular}> {{
    return this.get<{singular}>(`/{table_name}/${{id}}`);
  }}

  async create{singular}(data: Create{singular}Input): Promise<{singular}> {{
    return this.post<{singular}>("/{table_name}", data);
  }}

  async update{singular}(id: string, data: Update{singular}Input): Promise<{singular}> {{
    return this.patch<{singular}>(`/{table_name}/${{id}}`, data);
  }}

  async delete{singular}(id: string): Promise<void> {{
    return this.delete(`/{table_name}/${{id}}`);
  }}

'''
        
        api_content += '''}

export const api = new AppApi();
export default api;
'''
        
        api_file = project_path / "src" / "services" / "appApi.ts"
        api_file.parent.mkdir(parents=True, exist_ok=True)
        api_file.write_text(api_content)
        
        return api_file
    
    def _generate_entity_views(self, project_path: Path, table_name: str, fields: dict) -> list[Path]:
        """Generate list and form views for an entity."""
        files = []
        type_name = self._pascal_case(table_name)
        singular = type_name[:-1] if type_name.endswith("s") and len(type_name) > 1 else type_name
        
        # Generate ListView
        list_view = self._generate_list_view(project_path, table_name, singular, fields)
        files.append(list_view)
        
        # Generate FormView (Create/Edit)
        form_view = self._generate_form_view(project_path, table_name, singular, fields)
        files.append(form_view)
        
        return files
    
    def _generate_list_view(self, project_path: Path, table_name: str, singular: str, fields: dict) -> Path:
        """Generate a list view component for an entity."""
        type_name = self._pascal_case(table_name)
        
        # Get field names for columns (exclude user_id and complex types)
        columns = []
        for field_name, field_def in fields.items():
            if field_name not in ["user_id"] and field_def.get("type") != "json":
                columns.append(field_name)
        
        view_content = f'''// ============================================================================
// {type_name} List View - Auto-generated by RationalBloks Frontend MCP
// ============================================================================

import {{ useState, useEffect }} from "react";
import {{ useNavigate }} from "react-router-dom";
import {{
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  CircularProgress,
  Chip,
}} from "@mui/material";
import {{ Add, Edit, Delete }} from "@mui/icons-material";
import {{ api }} from "../../services/appApi";
import type {{ {singular} }} from "../../types/generated";

export default function {type_name}View() {{
  const navigate = useNavigate();
  const [items, setItems] = useState<{singular}[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    loadData();
  }}, []);

  async function loadData() {{
    try {{
      setLoading(true);
      const data = await api.get{type_name}();
      setItems(data || []);
    }} catch (err) {{
      setError(err instanceof Error ? err.message : "Failed to load data");
    }} finally {{
      setLoading(false);
    }}
  }}

  async function handleDelete(id: string) {{
    if (!confirm("Are you sure you want to delete this item?")) return;
    try {{
      await api.delete{singular}(id);
      setItems(items.filter((item) => item.id !== id));
    }} catch (err) {{
      setError(err instanceof Error ? err.message : "Failed to delete");
    }}
  }}

  if (loading) {{
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }}

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={{3}}>
        <Typography variant="h4" fontWeight="bold">
          {type_name}
        </Typography>
        <Button
          variant="contained"
          startIcon={{<Add />}}
          onClick={{() => navigate("/{table_name}/new")}}
        >
          Add {singular}
        </Button>
      </Box>

      {{error && (
        <Typography color="error" mb={{2}}>
          {{error}}
        </Typography>
      )}}

      <TableContainer component={{Paper}}>
        <Table>
          <TableHead>
            <TableRow>
'''
        # Add column headers
        for col in columns[:5]:  # Limit to 5 columns
            view_content += f'              <TableCell>{self._pascal_case(col)}</TableCell>\n'
        view_content += '''              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id} hover>
'''
        # Add column cells
        for col in columns[:5]:
            field_def = fields.get(col, {})
            if field_def.get("enum"):
                view_content += f'                <TableCell><Chip label={{item.{col}}} size="small" /></TableCell>\n'
            elif field_def.get("type") == "boolean":
                view_content += f'                <TableCell>{{item.{col} ? "Yes" : "No"}}</TableCell>\n'
            elif field_def.get("type") in ["date", "datetime"]:
                view_content += f'                <TableCell>{{item.{col} ? new Date(item.{col}).toLocaleDateString() : "-"}}</TableCell>\n'
            else:
                view_content += f'                <TableCell>{{item.{col}}}</TableCell>\n'
        
        view_content += f'''                <TableCell align="right">
                  <IconButton onClick={{() => navigate(`/{table_name}/${{item.id}}/edit`)}}>
                    <Edit />
                  </IconButton>
                  <IconButton onClick={{() => handleDelete(item.id)}} color="error">
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            )}}
            {{items.length === 0 && (
              <TableRow>
                <TableCell colSpan={{{len(columns[:5]) + 1}}} align="center">
                  No {table_name} found. Click "Add {singular}" to create one.
                </TableCell>
              </TableRow>
            )}}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}}
'''
        
        view_file = project_path / "src" / "components" / "views" / f"{type_name}View.tsx"
        view_file.parent.mkdir(parents=True, exist_ok=True)
        view_file.write_text(view_content)
        
        return view_file
    
    def _generate_form_view(self, project_path: Path, table_name: str, singular: str, fields: dict) -> Path:
        """Generate a create/edit form view for an entity."""
        type_name = self._pascal_case(table_name)
        
        # Filter editable fields
        editable_fields = {k: v for k, v in fields.items() if k not in ["user_id"]}
        
        view_content = f'''// ============================================================================
// {singular} Form View - Auto-generated by RationalBloks Frontend MCP
// ============================================================================

import {{ useState, useEffect }} from "react";
import {{ useNavigate, useParams }} from "react-router-dom";
import {{
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  CircularProgress,
  Alert,
}} from "@mui/material";
import {{ Save, ArrowBack }} from "@mui/icons-material";
import {{ api }} from "../../services/appApi";
import type {{ Create{singular}Input }} from "../../types/generated";

export default function {singular}FormView() {{
  const navigate = useNavigate();
  const {{ id }} = useParams<{{ id: string }}>();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<Create{singular}Input>({{
'''
        # Initialize form fields
        for field_name, field_def in editable_fields.items():
            default = self._get_default_value(field_def)
            view_content += f'    {field_name}: {default},\n'
        
        view_content += f'''  }});

  useEffect(() => {{
    if (isEdit && id) {{
      loadData(id);
    }}
  }}, [id, isEdit]);

  async function loadData(itemId: string) {{
    try {{
      setLoading(true);
      const data = await api.get{singular}(itemId);
      setFormData({{
'''
        for field_name in editable_fields.keys():
            view_content += f'        {field_name}: data.{field_name},\n'
        
        view_content += f'''      }});
    }} catch (err) {{
      setError(err instanceof Error ? err.message : "Failed to load data");
    }} finally {{
      setLoading(false);
    }}
  }}

  async function handleSubmit(e: React.FormEvent) {{
    e.preventDefault();
    try {{
      setSaving(true);
      setError(null);
      if (isEdit && id) {{
        await api.update{singular}(id, formData);
      }} else {{
        await api.create{singular}(formData);
      }}
      navigate("/{table_name}");
    }} catch (err) {{
      setError(err instanceof Error ? err.message : "Failed to save");
    }} finally {{
      setSaving(false);
    }}
  }}

  function handleChange(field: keyof Create{singular}Input, value: unknown) {{
    setFormData((prev) => ({{ ...prev, [field]: value }}));
  }}

  if (loading) {{
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }}

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={{2}} mb={{3}}>
        <Button startIcon={{<ArrowBack />}} onClick={{() => navigate("/{table_name}")}}>
          Back
        </Button>
        <Typography variant="h4" fontWeight="bold">
          {{isEdit ? "Edit" : "New"}} {singular}
        </Typography>
      </Box>

      {{error && (
        <Alert severity="error" sx={{{{ mb: 2 }}}}>
          {{error}}
        </Alert>
      )}}

      <Paper sx={{{{ p: 3 }}}}>
        <form onSubmit={{handleSubmit}}>
          <Box display="flex" flexDirection="column" gap={{3}}>
'''
        # Generate form fields
        for field_name, field_def in editable_fields.items():
            field_type = field_def.get("type", "string")
            required = field_def.get("required", False)
            enum_values = field_def.get("enum", [])
            
            if enum_values:
                # Select dropdown for enum
                view_content += f'''            <FormControl fullWidth{' required' if required else ''}>
              <InputLabel>{self._pascal_case(field_name)}</InputLabel>
              <Select
                value={{formData.{field_name} || ""}}
                label="{self._pascal_case(field_name)}"
                onChange={{(e) => handleChange("{field_name}", e.target.value)}}
              >
'''
                for val in enum_values:
                    view_content += f'                <MenuItem value="{val}">{self._pascal_case(val)}</MenuItem>\n'
                view_content += '''              </Select>
            </FormControl>

'''
            elif field_type == "boolean":
                view_content += f'''            <FormControlLabel
              control={{
                <Switch
                  checked={{Boolean(formData.{field_name})}}
                  onChange={{(e) => handleChange("{field_name}", e.target.checked)}}
                />
              }}
              label="{self._pascal_case(field_name)}"
            />

'''
            elif field_type == "text":
                view_content += f'''            <TextField
              label="{self._pascal_case(field_name)}"
              value={{formData.{field_name} || ""}}
              onChange={{(e) => handleChange("{field_name}", e.target.value)}}
              multiline
              rows={{4}}
              fullWidth
              {' required' if required else ''}
            />

'''
            elif field_type in ["date", "datetime"]:
                view_content += f'''            <TextField
              label="{self._pascal_case(field_name)}"
              type="{'datetime-local' if field_type == 'datetime' else 'date'}"
              value={{formData.{field_name} || ""}}
              onChange={{(e) => handleChange("{field_name}", e.target.value)}}
              fullWidth
              InputLabelProps={{{{ shrink: true }}}}
              {' required' if required else ''}
            />

'''
            elif field_type in ["integer", "decimal"]:
                view_content += f'''            <TextField
              label="{self._pascal_case(field_name)}"
              type="number"
              value={{formData.{field_name} || ""}}
              onChange={{(e) => handleChange("{field_name}", {'parseFloat' if field_type == 'decimal' else 'parseInt'}(e.target.value) || 0)}}
              fullWidth
              {' required' if required else ''}
            />

'''
            else:  # string
                view_content += f'''            <TextField
              label="{self._pascal_case(field_name)}"
              value={{formData.{field_name} || ""}}
              onChange={{(e) => handleChange("{field_name}", e.target.value)}}
              fullWidth
              {' required' if required else ''}
            />

'''
        
        view_content += f'''            <Box display="flex" gap={{2}} justifyContent="flex-end">
              <Button variant="outlined" onClick={{() => navigate("/{table_name}")}}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                startIcon={{saving ? <CircularProgress size={{20}} /> : <Save />}}
                disabled={{saving}}
              >
                {{saving ? "Saving..." : "Save"}}
              </Button>
            </Box>
          </Box>
        </form>
      </Paper>
    </Box>
  );
}}
'''
        
        form_file = project_path / "src" / "components" / "views" / f"{singular}FormView.tsx"
        form_file.write_text(view_content)
        
        return form_file
    
    def _get_default_value(self, field_def: dict) -> str:
        """Get default value for form field."""
        if "default" in field_def:
            default = field_def["default"]
            if isinstance(default, str):
                return f'"{default}"'
            return str(default).lower()
        
        field_type = field_def.get("type", "string")
        if field_type == "boolean":
            return "false"
        if field_type in ["integer", "decimal"]:
            return "0"
        return '""'
    
    def _generate_dashboard(self, project_path: Path, app_name: str, schema: dict) -> Path:
        """Generate a dashboard view with stats for each entity."""
        view_content = f'''// ============================================================================
// Dashboard View - Auto-generated by RationalBloks Frontend MCP
// ============================================================================

import {{ useState, useEffect }} from "react";
import {{ useNavigate }} from "react-router-dom";
import {{
  Box,
  Typography,
  Grid,
  Paper,
  CircularProgress,
}} from "@mui/material";
import {{ api }} from "../../services/appApi";

interface Stats {{
'''
        for table_name in schema.keys():
            view_content += f'  {table_name}Count: number;\n'
        
        view_content += f'''}}

export default function DashboardView() {{
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Stats>({{
'''
        for table_name in schema.keys():
            view_content += f'    {table_name}Count: 0,\n'
        
        view_content += f'''  }});

  useEffect(() => {{
    loadStats();
  }}, []);

  async function loadStats() {{
    try {{
      setLoading(true);
      const ['''
        
        view_content += ", ".join(f'{table_name}Data' for table_name in schema.keys())
        
        view_content += '''] = await Promise.all([
'''
        for table_name in schema.keys():
            type_name = self._pascal_case(table_name)
            view_content += f'        api.get{type_name}(),\n'
        
        view_content += '''      ]);
      setStats({
'''
        for table_name in schema.keys():
            view_content += f'        {table_name}Count: {table_name}Data?.length || 0,\n'
        
        view_content += f'''      }});
    }} catch (err) {{
      console.error("Failed to load stats:", err);
    }} finally {{
      setLoading(false);
    }}
  }}

  if (loading) {{
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }}

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" mb={{3}}>
        {app_name} Dashboard
      </Typography>

      <Grid container spacing={{3}}>
'''
        for table_name in schema.keys():
            type_name = self._pascal_case(table_name)
            view_content += f'''        <Grid item xs={{12}} sm={{6}} md={{4}}>
          <Paper
            sx={{{{
              p: 3,
              cursor: "pointer",
              transition: "transform 0.2s",
              "&:hover": {{ transform: "scale(1.02)" }},
            }}}}
            onClick={{() => navigate("/{table_name}")}}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {type_name}
            </Typography>
            <Typography variant="h3" fontWeight="bold">
              {{stats.{table_name}Count}}
            </Typography>
          </Paper>
        </Grid>

'''
        
        view_content += '''      </Grid>
    </Box>
  );
}
'''
        
        dashboard_file = project_path / "src" / "components" / "views" / "DashboardView.tsx"
        dashboard_file.write_text(view_content)
        
        return dashboard_file
    
    def _update_routes(self, project_path: Path, schema: dict) -> None:
        """Update App.tsx with routes for generated views."""
        app_file = project_path / "src" / "App.tsx"
        
        # Generate imports
        imports = ['import DashboardView from "./components/views/DashboardView";']
        routes = ['          <Route path="/dashboard" element={<DashboardView />} />']
        
        for table_name in schema.keys():
            type_name = self._pascal_case(table_name)
            singular = type_name[:-1] if type_name.endswith("s") and len(type_name) > 1 else type_name
            
            imports.append(f'import {type_name}View from "./components/views/{type_name}View";')
            imports.append(f'import {singular}FormView from "./components/views/{singular}FormView";')
            
            routes.append(f'          <Route path="/{table_name}" element={{<{type_name}View />}} />')
            routes.append(f'          <Route path="/{table_name}/new" element={{<{singular}FormView />}} />')
            routes.append(f'          <Route path="/{table_name}/:id/edit" element={{<{singular}FormView />}} />')
        
        # Read existing App.tsx
        if app_file.exists():
            content = app_file.read_text()
            
            # Find where to insert imports (after last import statement)
            import_section = "\n".join(imports)
            route_section = "\n".join(routes)
            
            # Create a new simplified App.tsx
            new_content = f'''// ============================================================================
// App.tsx - Auto-generated by RationalBloks Frontend MCP
// ============================================================================

import {{ BrowserRouter, Routes, Route, Navigate }} from "react-router-dom";
import {{ ThemeProvider, CssBaseline, Box }} from "@mui/material";
import {{ GoogleOAuthProvider }} from "@react-oauth/google";
import {{ createAppProvider }} from "@rationalbloks/universalfront";

import createAppTheme from "./theme/createAppTheme";
import Navbar from "./components/shared/Navbar";
import "./styles/globals.css";

// Generated view imports
{import_section}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const theme = createAppTheme();

// Create auth provider from universalfront
const {{ AuthProvider, useAuth }} = createAppProvider({{
  apiBaseUrl: import.meta.env.VITE_BUSINESS_LOGIC_API_URL || "https://logicblok.rationalbloks.com",
}});

function AppContent() {{
  const {{ isAuthenticated, isLoading }} = useAuth();

  if (isLoading) {{
    return <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">Loading...</Box>;
  }}

  return (
    <Box sx={{{{ display: "flex", flexDirection: "column", minHeight: "100vh" }}}}>
      <Navbar />
      <Box component="main" sx={{{{ flexGrow: 1, p: 3 }}}}>
        <Routes>
          {{/* Public routes */}}
          <Route path="/" element={{isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />}} />
          
          {{/* Protected routes */}}
{route_section}
          
          {{/* Fallback */}}
          <Route path="*" element={{<Navigate to="/dashboard" />}} />
        </Routes>
      </Box>
    </Box>
  );
}}

export default function App() {{
  return (
    <GoogleOAuthProvider clientId={{GOOGLE_CLIENT_ID}}>
      <ThemeProvider theme={{theme}}>
        <CssBaseline />
        <BrowserRouter>
          <AuthProvider>
            <AppContent />
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </GoogleOAuthProvider>
  );
}}
'''
            app_file.write_text(new_content)
    
    def _update_navbar(self, project_path: Path, app_name: str, schema: dict) -> None:
        """Update Navbar configuration with app-specific navigation."""
        navbar_config = project_path / "src" / "config" / "Navbar.tsx"
        
        nav_items = [{"label": "Dashboard", "path": "/dashboard"}]
        for table_name in schema.keys():
            type_name = self._pascal_case(table_name)
            nav_items.append({"label": type_name, "path": f"/{table_name}"})
        
        config_content = f'''// ============================================================================
// Navbar Configuration - Auto-generated by RationalBloks Frontend MCP
// ============================================================================

export const APP_NAME = "{app_name}";

export interface NavItem {{
  label: string;
  path: string;
}}

export const NAV_ITEMS: NavItem[] = {json.dumps(nav_items, indent=2)};
'''
        
        navbar_config.parent.mkdir(parents=True, exist_ok=True)
        navbar_config.write_text(config_content)
    
    def _cleanup_template_files(self, project_path: Path) -> None:
        """Remove template-specific files that don't apply to the generated app."""
        views_dir = project_path / "src" / "components" / "views"
        
        # Files to remove (rationalbloks-specific)
        files_to_remove = [
            "ProjectsView.tsx",
            "ProjectSettingsView.tsx",
            "BillingView.tsx",
            "TemplatesView.tsx",
            "DocumentationViewNew.tsx",
            "JsonSchemaIDE.tsx",
            "PaymentSuccessView.tsx",
            "PaymentCancelView.tsx",
            "SupportView.tsx",
        ]
        
        for filename in files_to_remove:
            file_path = views_dir / filename
            if file_path.exists():
                file_path.unlink()
    
    def _update_package_json(self, project_path: Path, name: str, description: str) -> None:
        """Update package.json with app-specific info."""
        pkg_file = project_path / "package.json"
        
        if pkg_file.exists():
            pkg = json.loads(pkg_file.read_text())
            pkg["name"] = self._slugify(name)
            pkg["description"] = description
            pkg["version"] = "1.0.0"
            pkg_file.write_text(json.dumps(pkg, indent=2))
    
    def _configure_env(self, project_path: Path, api_url: str) -> None:
        """Configure .env file with API URL."""
        env_file = project_path / ".env"
        env_example = project_path / ".env.example"
        
        if env_example.exists() and not env_file.exists():
            shutil.copy(env_example, env_file)
        
        if env_file.exists():
            content = env_file.read_text()
            lines = content.split("\n")
            new_lines = []
            updated = False
            
            for line in lines:
                if line.startswith("VITE_DATABASE_API_URL="):
                    new_lines.append(f"VITE_DATABASE_API_URL={api_url}")
                    updated = True
                else:
                    new_lines.append(line)
            
            if not updated:
                new_lines.append(f"VITE_DATABASE_API_URL={api_url}")
            
            env_file.write_text("\n".join(new_lines))
    
    def _run_npm_install(self, project_path: Path) -> dict:
        """Run npm install in the project directory."""
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            if result.returncode == 0:
                return {"success": True}
            else:
                return {"success": False, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "npm install timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
